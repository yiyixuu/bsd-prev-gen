import tkinter as tk
from tkinter import ttk
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
import time
import random
from selenium.webdriver.common.keys import Keys

class SearchBarApp:
    search_text = ""
    preferred_manufacturers = ["moog", "timken", "skf", "ultra-power", "wjb", "durago"]
    valid_previous_years = set()
    current_fitment_info = {}
    def __init__(self, root):
        self.root = root
        self.root.title("Search Bar")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize driver as None - will be created when needed
        self.driver = None
        
        # Center the window on screen and make it larger to accommodate results
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Create and configure entry widget (search bar)
        self.text_input = ttk.Entry(search_frame, width=50)
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Create search button
        self.search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=1)

        # Create results text widget
        self.results_text = tk.Text(main_frame, wrap=tk.WORD, width=80, height=30)
        self.results_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar for results
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.results_text['yscrollcommand'] = scrollbar.set

        # Bind Enter key to search function
        self.text_input.bind('<Return>', lambda event: self.perform_search())

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        search_frame.columnconfigure(0, weight=1)
        
        # Bind window closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def display_results(self, results_list):
        """Display results in the text widget"""
        self.results_text.delete('1.0', tk.END)  # Clear previous results
        
        if not results_list:
            self.results_text.insert(tk.END, "No results found.\n")
            return
            
        # Add header
        self.results_text.insert(tk.END, "Search Results:\n", "header")
        self.results_text.insert(tk.END, "-" * 80 + "\n\n")
        
        # Add each result
        for make, model, start_year, end_year in results_list:
            result_text = f"Make: {make}\n"
            result_text += f"Model: {model}\n"
            result_text += f"Year Range: {start_year}-{end_year}\n"
            result_text += "-" * 40 + "\n\n"
            
            self.results_text.insert(tk.END, result_text)
        
        self.results_text.see('1.0')  # Scroll to top

    def setup_driver(self, headless=True):
        """Initialize the WebDriver with the specified mode."""
        if self.driver:
            self.driver.quit()  # Close existing driver if any
            
        try:
            # Configure browser options
            options = Options()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            if headless:
                options.add_argument("--headless")  # Run in headless mode
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.logger.info(f"Selenium WebDriver initialized successfully in {'headless' if headless else 'visible'} mode")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            self.driver = None
            return False

    def check_previous_year_model(self, make, model, year):
        """Check if a model exists for the previous year"""
        try:
            # Navigate to the catalog for the previous year
            prev_year = str(int(year) - 1)
            self.results_text.insert(tk.END, f"Checking previous year model: {make} {model} {prev_year}\n")
            self.logger.info(f"Navigating to {make} {model} catalog...")
            
            self.driver.get("https://www.rockauto.com/")
            input_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]')))
            input_element.send_keys(f'{make} {model}')
            
            time.sleep(.5)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')))
            click_total = self.driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
            self.logger.info(f"Found {len(click_total)} autocomplete results")

            # Extract years from autocomplete results
            valid_years = []
            for result in click_total:
                # Split text and look for year-like strings (4 digits)
                words = result.text.split()
                for word in words:
                    if word.isdigit() and len(word) == 4:
                        valid_years.append(word)

            if prev_year in valid_years:
                self.logger.info(f"Found previous year model: {make} {model} {prev_year}")
                # Add to set - duplicates will automatically be handled
                self.valid_previous_years.add(f"{make} {model} {prev_year}")
                self.logger.info(f"Updated valid_previous_years: {self.valid_previous_years}")
                return True
            else:
                self.logger.info(f"Previous year model not found: {make} {model} {prev_year}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking previous year model: {str(e)}")
            # Get the current page source for debugging
            self.logger.info(f"Current page content: {self.driver.page_source[:500]}...")
            return False

    def classify_input(self, input_text):
        """
        Classify the input text as either a part number or position/car description.
        Returns: ('part_number', text) or ('position_car', text)
        """
        # Check if input matches position and car pattern
        # Position should be Front/Rear followed by tab and year range with car make/model
        if '\t' in input_text and any(pos in input_text.lower() for pos in ['front', 'rear']):
            return ('position_car', input_text)
        
        # Otherwise treat as part number (alphanumeric)
        return ('part_number', input_text)

    def perform_search(self):
        # Clear previous results
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert(tk.END, "Searching...\n")
        self.root.update()

        # Initialize driver in headless mode if it doesn't exist
        if not self.driver and not self.setup_driver(headless=True):
            self.display_results([])
            return
        
        self.search_text = self.text_input.get()
        input_type, search_text = self.classify_input(self.search_text)
        
        if input_type == 'part_number':
            self.perform_part_number_search(search_text)
        else:
            self.perform_position_car_search(search_text.split('\t')[0], search_text.split('\t')[1])

    def parse_car_description(self, description):
        """
        Parse a car description in the format 'XX~YY Make Model' or 'XX Make Model'
        Handles special cases:
        - Mercedes~Benz or MBZ
        - Model names with ~ (e.g. F~150, F~250)
        Returns: (make, model, start_year, end_year)
        """
        try:
            # Split into parts but preserve the original string
            parts = description.strip().split(' ', 1)
            if len(parts) < 2:
                raise ValueError(f"Invalid car description format: {description}")
                
            year_part = parts[0]
            make_model_part = parts[1]
            
            # Parse year part - only split on ~ if it's between two 2-digit numbers
            if '~' in year_part and len(year_part) == 5 and year_part[2] == '~':
                start_year_str, end_year_str = year_part.split('~')
                if start_year_str.isdigit() and end_year_str.isdigit():
                    start_year = '20' + start_year_str if int(start_year_str) < 50 else '19' + start_year_str
                    end_year = '20' + end_year_str if int(end_year_str) < 50 else '19' + end_year_str
                else:
                    raise ValueError(f"Invalid year format: {year_part}")
            else:
                if not year_part.isdigit():
                    raise ValueError(f"Invalid year format: {year_part}")
                start_year = '20' + year_part if int(year_part) < 50 else '19' + year_part
                end_year = start_year
            
            # Handle special cases in make/model
            if 'MBZ' in make_model_part:
                make_model_part = make_model_part.replace('MBZ', 'Mercedes Benz')
            elif 'Mercedes~Benz' in make_model_part:
                make_model_part = make_model_part.replace('Mercedes~Benz', 'Mercedes Benz')
                
            # Split make and model, handling special cases
            if ' ' not in make_model_part:
                raise ValueError(f"Invalid make/model format: {make_model_part}")
                
            make_model_parts = make_model_part.split(' ', 1)
            make = make_model_parts[0]
            model = make_model_parts[1]
            
            # Handle special model cases (e.g., F~150, F~250)
            if '~' in model:
                # Don't split the ~ in model numbers
                model = model.replace('~', '')
            
            self.logger.info(f"Parsed car description: {make} {model} ({start_year}-{end_year})")
            return make, model, start_year, end_year
            
        except Exception as e:
            self.logger.error(f"Error parsing car description '{description}': {str(e)}")
            return None, None, None, None

    def find_position_fitment(self, make, model, year, position):
        """
        Find fitment information for a specific position (front/rear).
        Returns the part number if found, None otherwise.
        """
        try:
            # Construct search string
            search_string = f"{make} {model} {year}"
            self.logger.info(f"Searching position fitment for: {search_string} ({position})")
            
            # Navigate to catalog
            self.driver.get("https://www.rockauto.com/en/catalog/")
            input_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]'))
            )
            input_element.send_keys(search_string)
            
            # Wait for and get autocomplete suggestions
            time.sleep(1)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr'))
            )
            engine_suggestions = self.driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
            engines = [suggestion.text.strip() for suggestion in engine_suggestions]
            if 'Vehicles' in engines:
                engines.remove('Vehicles')

            self.logger.info(f"Found {len(engines)} engine types")
            
            for engine in engines:
                self.logger.info(f"Checking engine: {engine}")
                self.driver.get("https://www.rockauto.com/en/catalog/")
                input_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]'))
                )
                input_element.send_keys(engine)
                time.sleep(0.25)
                input_element.send_keys(Keys.ENTER)
                input_element.send_keys(Keys.ENTER)

                car_part_found = False

                try:
                    # Find Brake & Wheel Hub with improved click handling
                    car_part = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Brake & Wheel Hub')]"))
                    )
                    # Scroll element into view
                    time.sleep(0.25)  # Wait for any animations to complete
                    
                    try:
                        # Try regular click first
                        car_part.click()
                    except Exception as click_error:
                        self.logger.info(f"Regular click failed, trying JavaScript click: {str(click_error)}")
                        # Try JavaScript click as fallback
                        self.driver.execute_script("arguments[0].click();", car_part)
                    
                    car_part_found = True
                except TimeoutException:
                    car_part_found = False

                if not car_part_found:
                    self.logger.info("Disambiguation found")
                    # Extract engine substring by removing make, model, year
                    engine_substring = ' '.join([word for word in engine.split() if word not in [make.lower(), model.lower(), str(year).lower()]])
                    self.logger.info(f"Engine substring: {engine_substring}")
                    try:
                        engine_disambiguation = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{engine_substring}')]"))
                        )
                        # Scroll element into view
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", engine_disambiguation)
                        time.sleep(0.5)
                        
                        try:
                            engine_disambiguation.click()
                        except Exception as click_error:
                            self.logger.info(f"Regular click failed, trying JavaScript click: {str(click_error)}")
                            self.driver.execute_script("arguments[0].click();", engine_disambiguation)
                            
                        car_part = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Brake & Wheel Hub')]"))
                        )
                        # Scroll and click with same pattern
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", car_part)
                        time.sleep(0.5)
                        
                        try:
                            car_part.click()
                        except Exception as click_error:
                            self.logger.info(f"Regular click failed, trying JavaScript click: {str(click_error)}")
                            self.driver.execute_script("arguments[0].click();", car_part)
                            
                        car_part_found = True
                    except TimeoutException:
                        self.logger.info(f"Could not find disambiguation for engine: {engine}")
                        continue

                if car_part_found:
                    try:
                        part_type = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Wheel Bearing & Hub')]"))
                        )
                        # Scroll and click with same pattern
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", part_type)
                        time.sleep(0.5)
                        
                        try:
                            part_type.click()
                        except Exception as click_error:
                            self.logger.info(f"Regular click failed, trying JavaScript click: {str(click_error)}")
                            self.driver.execute_script("arguments[0].click();", part_type)
                        
                        # Apply position filter
                        input_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'filter-input'))
                        )
                        input_element.send_keys(position)
                        input_element.send_keys(Keys.ENTER)
                        
                        # Check if there are any results after filtering
                        try:
                            product_listings = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_all_elements_located((By.XPATH, '//table[contains(@class, "nobmp")]/tbody/tr'))
                            )
                            
                            # Look for part numbers from preferred manufacturers
                            for manufacturer in self.preferred_manufacturers:
                                for row in product_listings:
                                    try:
                                        row_text = row.text.lower()
                                        if manufacturer in row_text:
                                            # Extract part number from the row
                                            part_number = row.find_element(By.CLASS_NAME, 'listing-final-partnumber').text.strip()
                                            manufacturer_name = row.find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.strip()
                                            self.logger.info(f"Found part number {part_number} from {manufacturer_name}")
                                            return part_number, manufacturer_name
                                    except Exception as e:
                                        self.logger.error(f"Error processing row: {str(e)}")
                                        continue
                            
                        except TimeoutException:
                            self.logger.info(f"No {position} fitment found for this engine")
                            
                    except TimeoutException:
                        self.logger.info(f"Could not access Wheel Bearing & Hub")
                        continue

            return None, None
            
        except Exception as e:
            self.logger.error(f"Error in find_position_fitment: {str(e)}")
            return None, None

    def perform_position_car_search(self, position, car_description):
        """Perform the position and car based search"""
        cars = car_description.split(",")
        # Clear previous results
        self.valid_previous_years.clear()
        found_any_previous = False
        
        for car in cars:
            make, model, start_year, end_year = self.parse_car_description(car)
            if not make:  # Skip if parsing failed
                continue
                
            self.logger.info(f"Checking previous year model for {make} {model} {start_year}")
            
            # Check for previous year model
            if self.check_previous_year_model(make, model, start_year):
                found_any_previous = True
                prev_year = int(start_year) - 1
                
                result_text = f"\nFound previous year model:\n"
                result_text += f"Make: {make}\n"
                result_text += f"Model: {model}\n"
                result_text += f"Year: {prev_year}\n"
                
                # Search for fitment in the previous year model
                part_number, manufacturer = self.find_position_fitment(make, model, prev_year, position)
                
                if part_number:
                    # Copy part number to clipboard using tkinter
                    self.root.clipboard_clear()
                    self.root.clipboard_append(part_number)
                    result_text += f"\nFound {position} fitment:\n"
                    result_text += f"Part Number: {part_number} (copied to clipboard)\n"
                    result_text += f"Manufacturer: {manufacturer}\n"
                    result_text += "-" * 40 + "\n"
                    self.results_text.insert(tk.END, result_text)
                    self.root.update()
                    # Stop processing if fitment is found
                    return
                else:
                    result_text += f"\nNo {position} fitment found\n"
                    result_text += "-" * 40 + "\n"
                    self.results_text.insert(tk.END, result_text)
                    self.root.update()
            else:
                result_text = f"No results for {int(start_year)-1} {make} {model}\n"
                self.results_text.insert(tk.END, result_text)
                self.root.update()
        
        # If we get here and haven't found any previous models
        if not found_any_previous:
            no_prev_message = "no previous generation"
            self.root.clipboard_clear()
            self.root.clipboard_append(no_prev_message)
            self.results_text.insert(tk.END, f"\n{no_prev_message} (copied to clipboard)\n")
            self.root.update()

    def perform_part_number_search(self, part_number):
        """Perform the original part number based search"""
            
        try:
            self.logger.info(f"Searching for part number: {part_number}")
            self.driver.get(f"https://www.rockauto.com/en/partsearch/?partnum={part_number}")
            
            # Wait for page listings
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'listings-container'))
                )
            except TimeoutException:
                self.logger.error("No listings found within timeout period")
                self.display_results([])
                return

            # Find all results in listing container
            all_results = self.driver.find_elements(By.XPATH, '//*[contains(@class, "listing-border-top-line listing-inner-content")]')
            if not all_results:
                self.logger.info("No results found.")
                self.display_results([])
                return

            # Choose listing by brand or fallback to first
            chosen_index = 0
            matched_brand = None
            
            # Try to find manufacturers in order of preference
            for preferred_brand in self.preferred_manufacturers:
                for i, result in enumerate(all_results):
                    try:
                        manufacturer = result.find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.lower()
                        category = (result.find_element(By.CLASS_NAME, 'listing-text-row').text)[10:]
                        if preferred_brand in manufacturer:
                            matched_brand = manufacturer
                            chosen_index = i
                            self.logger.info(f"Matched preferred brand '{manufacturer}' at index {i}")
                            self.logger.info(f"Category: {category}")
                            break
                    except NoSuchElementException:
                        continue
                if matched_brand:  # If we found a match, stop searching
                    break

            # Click part number to open popup
            try:
                chosen_item = all_results[chosen_index]
                part_link = chosen_item.find_element(By.XPATH, './/*[contains(@id, "vew_partnumber")]')
                part_link.click()
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table'))
                )
                model_car_lst = self.driver.find_elements(By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table/tbody/tr')
            except Exception as e:
                self.logger.error(f"Error opening part details - {str(e)}")
                self.display_results([])
                return
            
            # Initialize arrays
            make = [0] * len(model_car_lst)
            model = [0] * len(model_car_lst)
            startyear = [0] * len(model_car_lst)
            endyear = [0] * len(model_car_lst)
            counter = 0

            for model_car in model_car_lst:
                car_make = model_car.find_element(By.XPATH, './td[1]').text
                make[counter] = car_make
                car_model = model_car.find_element(By.XPATH, './td[2]').text
                model[counter] = car_model
                car_year = model_car.find_element(By.XPATH, './td[3]').text

                if "-" in car_year:
                    years = car_year.split("-")
                    startyear[counter] = years[0].strip()
                    endyear[counter] = years[1].strip()
                else:
                    startyear[counter] = car_year.strip()
                    endyear[counter] = car_year.strip()

                counter = counter + 1

            #close dialog box
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'dialog-close'))).click()

            # Create results list
            results = []
            for i in range(len(make)):
                results.append((make[i], model[i], startyear[i], endyear[i]))
            
            # Display results in the text widget
            self.display_results(results)

            # Search for previous version of each model
            self.results_text.insert(tk.END, "\nChecking previous year models...\n")
            self.root.update()

            found_any_previous = False  # Track if we found any previous models
            
            models_with_previous = []
            for make, model, startyear, endyear in results:
                if self.check_previous_year_model(make, model, startyear):
                    found_any_previous = True
                    result_text = f"\nFound previous year model:\n"
                    result_text += f"Make: {make}\n"
                    result_text += f"Model: {model}\n"
                    result_text += f"Year: {int(startyear)-1}\n"
                    result_text += "-" * 40 + "\n"
                    models_with_previous.append((make, model, random.randint(int(startyear), int(endyear))))
                    self.results_text.insert(tk.END, result_text)
                    self.root.update()
                else:
                    result_text = f"No results for {int(startyear)-1} {make} {model}\n"
                    self.results_text.insert(tk.END, result_text)
                    self.root.update()

            
            if not found_any_previous:
                self.results_text.insert(tk.END, "No previous generation\n")    
                self.root.update()
            else:
                try:
                    for make, model, year in models_with_previous:
                        self.logger.info(f"Finding fitment for {make} {model} {year}...")
                        fitment_info = self.find_fitment(make, model, year)
                        
                        # Process and display the fitment info
                        formatted_result = self.process_fitment_info(fitment_info, make, model, year)
                        self.results_text.insert(tk.END, formatted_result)
                        self.root.update()

                    # Display final results after all searches are complete
                    self.results_text.insert(tk.END, "\nFinal Results:\n")
                    self.results_text.insert(tk.END, "-" * 40 + "\n")
                    
                    self.logger.info(f"Before final display - valid_previous_years: {self.valid_previous_years}")
                    self.logger.info(f"Before final display - current_fitment_info: {self.current_fitment_info}")
                    
                    for prev_model in self.valid_previous_years:
                        # Split the previous year model string into components
                        prev_make, prev_model_name, prev_year = prev_model.split()
                        self.logger.info(f"Processing previous model: {prev_model}")
                        
                        # Find the current year fitment by constructing the key
                        for current_key in self.current_fitment_info:
                            current_make, current_model, current_year = current_key.split()
                            self.logger.info(f"Checking against current key: {current_key}")
                            if current_make == prev_make and current_model == prev_model_name:
                                position, drive_type = self.current_fitment_info[current_key]
                                self.logger.info(f"Found match! Adding to display: {prev_year} {prev_make} {prev_model_name}")
                                self.results_text.insert(tk.END, f"{prev_year} {prev_make} {prev_model_name}\n")
                                self.results_text.insert(tk.END, f"Current fitment ({current_year}): {position}, {drive_type}\n")
                                self.results_text.insert(tk.END, "-" * 40 + "\n")
                                break
                    
                    self.root.update()

                except Exception as e:
                    self.logger.error(f"Search failed: {str(e)}")
                    self.display_results([])

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            self.display_results([])

    def on_closing(self):
        if self.driver:
            self.logger.info("Closing WebDriver")
            self.driver.quit()
        self.root.destroy()

    def find_fitment(self, make, model, year):
        fitment_info = {} # fitment info is a dict with key: engine, value: drive info
        try:
            # Construct search string
            search_string = f"{make} {model} {year}"
            self.logger.info(f"Searching fitment for: {search_string}...")
            
            # Navigate to catalog
            self.driver.get("https://www.rockauto.com/en/catalog/")
            input_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]'))
            )
            input_element.send_keys(search_string)
            
            
            # Wait for and get autocomplete suggestions
            time.sleep(1)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr'))
            )
            engine_suggestions = self.driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
            # Convert engine suggestions to list of strings and remove 'Vehicles' element
            engines = [suggestion.text.strip() for suggestion in engine_suggestions]
            if 'Vehicles' in engines:
                engines.remove('Vehicles')

            self.logger.info(f"Engines: {engines}")

            for engine in engines:
                self.logger.info(f"Searching for {engine}")
                self.driver.get("https://www.rockauto.com/en/catalog/")
                input_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]'))
                )
                input_element.send_keys(engine)
                time.sleep(0.25)
                input_element.send_keys(Keys.ENTER)
                input_element.send_keys(Keys.ENTER)

                car_part_found = False

                try:
                    # Now proceed with finding Brake & Wheel Hub
                    car_part = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Brake & Wheel Hub')]"))
                    )
                    car_part_found = True
                except TimeoutException:
                    car_part_found = False

                if not car_part_found:
                    self.logger.info("Disambiguation found")
                    # Extract engine substring by removing make, model, year
                    engine_substring = ' '.join([word for word in engine.split() if word not in [make.lower(), model.lower(), str(year).lower()]])
                    self.logger.info(f"Engine substring: {engine_substring}")
                    engine_disambiguation = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{engine_substring}')]"))
                    )
                    engine_disambiguation.click()
                    car_part = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Brake & Wheel Hub')]"))
                    )
                    car_part_found = True

                if car_part_found:
                    car_part.click()
                    part_type = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{"Wheel Bearing & Hub"}')]")))
                    if part_type:
                        part_type.click()
                        input_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'filter-input')))
                        if input_element:
                            # self.logger.info(f"Found filter search: {input_element}")
                            input_element.send_keys(self.search_text)
                            input_element.send_keys(Keys.ENTER)
                            self.logger.info(f"Searching: {self.search_text}")
                           
                            #goes into table and extracts row
                            product_listings = self.driver.find_elements(By.XPATH, '//table[contains(@class, "nobmp")]/tbody/tr')
                            # self.logger.info(f"Product listings: {product_listings}")

                            for index, row in enumerate(product_listings):
                                row_text = row.text.lower()
                                if any(brand in row_text for brand in self.preferred_manufacturers):
                                    # self.logger.info(f"Row text: {row_text}")
                                    # parse the row text to get the fitment info
                                    manufacturer = row.find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.strip()
                                    drive_info = row.find_element(By.XPATH, './/div[@class="listing-text-row"]').text
                                    self.logger.info(f"Manufacturer: {manufacturer}")
                                    self.logger.info(f"Drive info: {drive_info}")
                                    fitment_info[engine] = drive_info

                        else:
                            self.logger.info(f"No filter search found")   
                    
            return fitment_info
        except Exception as e:
            self.logger.error(f"Error in find_fitment: {str(e)}")
            self.results_text.insert(tk.END, "\nError occurred while checking fitment\n")
            self.root.update()

    def process_fitment_info(self, fitment_info, make, model, year):
        """Process the fitment information and return a formatted string for display."""
        if not fitment_info:
            return f"No fitment information found for {year} {make} {model}\n"
            
        # Get the first drive info text (they should all be the same for a given model)
        drive_info = next(iter(fitment_info.values())).lower()
        
        # Determine position (front/rear)
        position = "front" if "front" in drive_info else "rear" if "rear" in drive_info else ""
        
        # Determine drive type
        drive_type = ""
        if "4wd" in drive_info or "4x4" in drive_info or "awd" in drive_info:
            drive_type = "4wd"
        elif "fwd" in drive_info or "front wheel drive" in drive_info:
            drive_type = "fwd"
        elif "rwd" in drive_info or "rear wheel drive" in drive_info:
            drive_type = "rwd"
            
        # Update current_fitment_info - store even if we only have partial info
        key = f"{make} {model} {year}"
        self.current_fitment_info[key] = (position, drive_type)
        self.logger.info(f"Added fitment info for {key}: {position}, {drive_type}")
        self.logger.info(f"Current fitment_info contents: {self.current_fitment_info}")
            
        # Build the output string for display
        result = f"Fitment for {year} {make} {model}:\n"
        
        # Group engines by their fitment info for display
        fitment_groups = {}
        for engine, info in fitment_info.items():
            if info in fitment_groups:
                fitment_groups[info].append(engine)
            else:
                fitment_groups[info] = [engine]
        
        # Display the grouped fitment info
        if len(fitment_groups) == 1:
            drive_info = list(fitment_groups.keys())[0]
            result += f"{drive_info}\n"
        else:
            for drive_info, engines in fitment_groups.items():
                if len(engines) > 1:
                    result += f"Engines ({', '.join(engines)}):\n"
                else:
                    result += f"Engine {engines[0]}:\n"
                result += f"  {drive_info}\n"
                
        return result

def main(testing_mode=False):
    root = tk.Tk()
    app = SearchBarApp(root)
    # If in testing mode, initialize the visible browser right away
    if testing_mode:
        app.setup_driver(headless=False)
    root.mainloop()

if __name__ == "__main__":
    # Set testing_mode=True to run with visible browser for testing
    main(testing_mode=True)
