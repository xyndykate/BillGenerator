try:
    import africastalking
except ImportError:
    print("Error: africastalking package is not installed.")
    print("Please install it using: pip install africastalking")
    exit(1)

import datetime
import os

class RentalBill:
    WATER_RATE = 200  # KES per cubic meter (updated from 50)
    PAYBILL_NUMBER = "522533"
    
    def __init__(self):
        """Initialize RentalBill with optional SMS functionality"""
        print("\nAfricasTalking SMS Configuration")
        print("-" * 50)
        print("1. Press Enter to skip SMS functionality")
        print("2. Enter credentials for SMS notifications")
        print("-" * 50)
        
        self.at_username = input("\nEnter Africastalking username: ").strip()
        if self.at_username:
            self.at_api_key = input("Enter Africastalking API key: ").strip()
            if not self.at_api_key:
                print("API key is required. SMS functionality will be disabled.")
                return
            self.initialize_sms()

    def initialize_sms(self):
        """Initialize Africastalking SMS service"""
        try:
            self.at = africastalking
            
            # Validate credentials before initialization
            if not self.at_username or not self.at_api_key:
                raise ValueError("Username and API key are required")
                
            # Initialize the SMS service
            self.at.initialize(
                username=self.at_username,
                api_key=self.at_api_key
            )
            
            self.sms = self.at.SMS
            
            # Test connection with balance check instead of sending message
            account = self.at.Application.fetch_application_data()
            print("\nConnection Status:")
            print("-" * 50)
            print(f"Username: {self.at_username}")
            print(f"Environment: {'Sandbox' if 'sandbox' in self.at_username.lower() else 'Production'}")
            print(f"Balance: {account.get('UserData', {}).get('balance', 'Unknown')}")
            
        except Exception as e:
            print(f"\nAuthentication Error: {str(e)}")
            self.at = None

    def get_tenant_info(self):
        """Collect tenant information and meter readings"""
        self.tenant_name = input("Enter tenant name: ")
        self.apt_number = input("Enter apartment number: ")
        self.rent_amount = float(input("Enter monthly rent amount (KES): "))
        self.prev_reading = float(input("Enter previous water meter reading: "))
        self.current_reading = float(input("Enter current water meter reading: "))
        phone = input("Enter tenant phone number (or press Enter to skip): ").strip()
        if phone:
            # Ensure phone number is in international format
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+254' + phone[1:]
                elif phone.startswith('7') or phone.startswith('1'):
                    phone = '+254' + phone
            self.phone_number = phone
        else:
            self.phone_number = ''

    def calculate_bill(self):
        """Calculate water usage and total bill"""
        self.water_usage = self.current_reading - self.prev_reading
        self.water_bill = self.water_usage * self.WATER_RATE
        self.total_amount = self.rent_amount + self.water_bill

    def generate_bill(self):
        """Generate formatted bill content"""
        current_date = datetime.datetime.now()
        month_year = current_date.strftime("%B %Y")
        
        bill_content = f"""
=================================================
                RENTAL BILL
=================================================
Date: {current_date.strftime("%d %B %Y")}
Billing Period: {month_year}

Tenant Name: {self.tenant_name}
Apartment Number: {self.apt_number}

BILL DETAILS:
-------------------------------------------------
Monthly Rent:             KES {self.rent_amount:.2f}
Water Usage ({self.water_usage:.1f} m³):    KES {self.water_bill:.2f}
-------------------------------------------------
Total Amount Due:         KES {self.total_amount:.2f}

PAYMENT INSTRUCTIONS:
-------------------------------------------------
Please pay via M-Pesa:
Paybill Number: {self.PAYBILL_NUMBER}
Account Number: 7944442#{self.apt_number}

Thank you for your prompt payment!
=================================================
"""
        return bill_content

    def save_bill(self, content):
        """Save bill to file"""
        filename = f"Bill_{self.apt_number}_{datetime.datetime.now().strftime('%B_%Y')}.txt"
        os.makedirs("bills", exist_ok=True)
        filepath = os.path.join("bills", filename)
        
        with open(filepath, "w") as file:
            file.write(content)
        return filepath

    def send_sms_notification(self):
        """Send bill summary via SMS"""
        if not hasattr(self, 'at') or not self.phone_number:
            print("SMS service not initialized or phone number missing")
            return

        # Debug logging
        print("\nSMS Delivery Details:")
        print("-" * 50)
        print(f"Phone Number: {self.phone_number}")
        print(f"Username: {self.at_username}")
        print(f"Environment: {'sandbox' if 'sandbox' in self.at_username.lower() else 'production'}")

        message = (
            f"Dear {self.tenant_name}, your {datetime.datetime.now().strftime('%B %Y')} "
            f"bill for Apt #{self.apt_number} is ready. "
            f"Total amount due: KES {self.total_amount:.2f}. "
            f"Please pay via M-Pesa Paybill {self.PAYBILL_NUMBER}, "
            f"Account: 7944442#{self.apt_number}"
        )

        try:
            print("\nAttempting to send SMS...")
            response = self.sms.send(message, [self.phone_number])
            print("\nAPI Response:")
            print("-" * 50)
            print(f"Response Data: {response}")
            
            if response and hasattr(response, 'SMSMessageData'):
                print(f"Message Count: {response['SMSMessageData']['MessageCount']}")
                print(f"Recipients: {response['SMSMessageData']['Recipients']}")
                
        except Exception as e:
            print(f"\nError Details:")
            print("-" * 50)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")

def main():
    bill = RentalBill()
    bill.get_tenant_info()
    bill.calculate_bill()
    bill_content = bill.generate_bill()
    saved_file = bill.save_bill(bill_content)
    print(f"\nBill has been saved to: {saved_file}")
    
    if hasattr(bill, 'at') and bill.phone_number:
        bill.send_sms_notification()

if __name__ == "__main__":
    main()