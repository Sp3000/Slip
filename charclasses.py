import string

classes = {"a": string.ascii_lowercase + string.ascii_uppercase,
           "c": "".join(c for c in string.ascii_lowercase + string.ascii_uppercase if
                        c.lower() not in "aeiou"),
           "d": string.digits,
           "h": string.hexdigits,
           "l": string.ascii_lowercase,
           "o": string.octdigits,
           "p": string.punctuation,
           "s": " \t\x0b\x0c", # Not \r\n
           "u": string.ascii_uppercase,
           "v": "aeiouAEIOU",
           "w": string.ascii_lowercase + string.ascii_uppercase + string.digits + "_",
           "y": "aeiouy"}
           
