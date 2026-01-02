import string
import random

def short_code_generator(length=6):
    short_code=""
    chars=string.ascii_letters+string.digits
    i=0
    while(i<length):
        short_code+=random.choice(chars)
        i+=1
    return short_code


