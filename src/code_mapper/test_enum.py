from enum import Enum
from java_code_parser_metadata import *

# Suppose you have a string you want to check
string_to_check = 'StringBuilder'

print(ObjectType.STRING_BUILDER)

# You can use the `Enum()` constructor to get the enum item
enum_item = ObjectType(string_to_check)
print(enum_item)

# You can use the new `Enum.str()` classmethod to check if the string is an enum value
if ObjectType.type_of_interest(string_to_check):
    # If the string is an enum value, you can get the enum item using `Enum()` constructor
    enum_item = ObjectType(string_to_check)
    print(f"The string is an enum value: {enum_item}")
else:
    print("The string is not an enum value.")