import time,csv,os,json,getpass
from datetime import datetime
try:
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except:
    modules = ['requests','selenium','webdriver_manager']
    for mod in modules:
        print("Installing {0}, please wait...n".format(mod))
        print("------------------------------------n")
        os.system("pip install {0}".format(mod))  
    try:
        import requests
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except:
        print('required modules not installed. please install them by opening command prompt or power shell. Copy and paste below command and press enter\n pip install requests selenium webdriver_manager')

if not os.path.exists('reports'):
    os.makedirs('reports')

def fetch_sms_data(api_url):
    try:
        response = requests.get(api_url+f"?username={username}&password={password}")
    except:
        print("Failed to fetch data from API")
        quit()
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Invalid username or password")
        quit()
    else:
        print("Internal server error")
        quit()

def setup_google_messages():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://messages.google.com/web/authentication")
    # Wait for manual QR code scan (user action required)
    input("\n\n***Scan the QR code and press Enter once you're ready...***\n\n")
    return driver

# Function to send SMS using Google Messages Web
def send_sms(driver, phone_number, message):
    start_chat_button = driver.find_element(By.XPATH, "//a[contains(@href, '/web/conversations/new')]")
    start_chat_button.click()
    to_field = driver.find_element(By.XPATH, "//input[@placeholder='Type a name, phone number, or email']")
    to_field.send_keys(phone_number)
    time.sleep(5)
    to_field.send_keys(Keys.ENTER)
    time.sleep(5)
    message_box = driver.find_element(By.XPATH, "//textarea[starts-with(@placeholder, 'Text message')]") 
    message_box.send_keys(message)
    message_box.send_keys(Keys.ENTER)

# Main function to process and send SMS
def process_sms_sending(alert_type,api_url):
    sms_data = fetch_sms_data(api_url)
    school_name=sms_data['school_name']
    total_messages = len(sms_data['data'])
    if total_messages==0:
        print('no message available to send')
        quit()
    print(f"Total number of messages: {total_messages}")
    while True:
        try:
            start_index = int(input(f"Start sending SMS from message no (1-{total_messages}): ")) - 1
            end_index = int(input(f"Send SMS upto message no (1-{total_messages}): ")) - 1
            # Validate that the indices are within the valid range
            if start_index < 0 or end_index >= total_messages or start_index > end_index or (end_index - start_index) > 80:   
                print("Invalid message no. Please enter valid start and end message no.")
            else:
                break
        except ValueError:
            print("Please enter valid integer values for start and end indices.")
    print(f"Sending messages starting from {start_index+1} upto {end_index+1}")
    driver = setup_google_messages()

    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if alert_type=='absentee_alerts':
        filename = f"absentee_alerts_{current_timestamp}_sms_report_{start_index + 1}_to_{end_index + 1}.csv"
    else:
        filename = f"fee_due_alerts_{current_timestamp}_sms_report_{start_index + 1}_to_{end_index + 1}.csv"
    with open('reports/' + filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['stu_id', 'stu_name', 'phone', 'status']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for  i in range(start_index, end_index + 1):
            sms=sms_data['data'][i]
            phone_number = sms.get('phone')
            if alert_type =='absentee_alerts':
                message = f"{sms.get('stu_name')} (Id {sms.get('stu_id')}) आज स्कूल में अनुपस्थित है। इस महीने कुल {sms.get('totalA')} अनुपस्थिति हो चुकी हैं। कृपया सुनिश्चित करें कि आपका बच्चा नियमित रूप से स्कूल आए, ताकि शैक्षणिक हानि से बचा जा सके। - {school_name}. https://{school_code}.matrixe.in?pp=1"
            else:
                message = f"{sms.get('stu_name')} (Id {sms.get('stu_id')}) की {sms.get('fee_due')} रुपये स्कूल फीस बकाया है। कृपया अपने बच्चे की स्कूल फीस समय पर जमा करें। - {school_name}. विजिट करें https://{school_code}.matrixe.in?pp=1"
            if phone_number and message and len(str(phone_number)) == 10 and str(phone_number) != '9999999999':
                print(f"Sending SMS to {phone_number}...", end="")
                try:
                    send_sms(driver, phone_number, message)
                    status = "success"
                    print('success')
                except Exception as e:
                    status = "failed"
                    print(f"failed. Error: {e}")
            else:
                print(f"Sending SMS to {phone_number}...failed. Error: Invalid phone number")
                status = "failed"
            writer.writerow({
                'stu_id': sms.get('stu_id'),
                'stu_name': sms.get('stu_name'),
                'phone': sms.get('phone'),
                'status': status
            })
    
    print(f"Report generated: {filename}")
    input("Press Enter to quit the browser...")
    driver.quit()

def get_user_info():
    global school_code, username
    school_code = input('Enter school code: ')
    username = input('Enter username: ')
    # Save school_code and username to a JSON file
    user_info = {
        "school_code": school_code,
        "username": username
    }
    with open('user_info.json', 'w') as f:
        json.dump(user_info, f, indent=4)
    print("Data saved successfully.")

# Main program
if not os.path.exists('start-app.bat'):
    with open('start-app.bat', 'w') as file:
        file.write("@echo off\npython send_sms.py\npause")

username=''
school_code=''

try:
    with open('user_info.json', 'r') as f:
        user_info = json.load(f)
        school_code = user_info['school_code']
        print('school code:',school_code)
        username = user_info['username']
        print('username:',username)
except:
    get_user_info()

choice=input('enter 1 to change user info or press enter to continue: ')
if choice=='1':
    get_user_info()
password = getpass.getpass(f"Enter password for {username}: ")
alerts=input('Which alerts you want to send?\n1. Absentees\n2. Fee Due\nEnter your choice: ')
if alerts=='1':
    api_url = f"https://{school_code}.example.com/attendance/absentees_api"
    # api_url = "http://127.0.0.1:8000/attendance/absentees_api"
    process_sms_sending('absentee_alerts',api_url)
elif alerts=='2':
    api_url = f"https://{school_code}.example.com/fee_record/pending_installments_api"
    # api_url = f"http://127.0.0.1:8000/fee_record/pending_installments_api"
    process_sms_sending('fee_due_alerts',api_url)
else:
    input('Invalid choice. Press enter to exit. ')