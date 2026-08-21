def validate_email(email):
    if "@" not in email or "." not in email:
        raise ValueError("Invalid email address.")

def validate_license_number(license_number):
    if not license_number.isalnum():
        raise ValueError("Driver's license number should only contain alphanumeric characters.")

def validate_rental_duration(rental_duration):
    if not rental_duration.isdigit() or int(rental_duration) <= 0:
        raise ValueError("Rental duration should be a positive integer.")

email = input("Enter your email address: ")
license_number = input("Enter your driver's license number: ")
rental_duration = input("Enter the rental duration in days: ")

try:
    validate_email(email)
    validate_license_number(license_number)
    validate_rental_duration(rental_duration)
    rental_duration = int(rental_duration)
    print("Reservation successful!")
except ValueError as error:
    print("Validation error:", str(error))
