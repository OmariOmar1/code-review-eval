def is_palindrome(text):
    """Check for a palindrome using only letters and digits, case-insensitively.

    >>> is_palindrome("A man, a plan, a canal: Panama")
    True
    >>> is_palindrome("race a car")
    False
    >>> is_palindrome("")
    True
    """
    cleaned = [char.lower() for char in text if char.isalnum()]
    return cleaned == cleaned[::-1]
