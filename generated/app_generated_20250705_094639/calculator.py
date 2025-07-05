class Calculator:
    """A simple calculator class to perform basic arithmetic operations."""

    def add(self, a: float, b: float) -> float:
        """Returns the sum of a and b.

        Args:
            a (float): The first number.
            b (float): The second number.

        Returns:
            float: The sum of a and b.
        """
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Returns the difference of a and b.

        Args:
            a (float): The first number.
            b (float): The second number.

        Returns:
            float: The difference of a and b.
        """
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Returns the product of a and b.

        Args:
            a (float): The first number.
            b (float): The second number.

        Returns:
            float: The product of a and b.
        """
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Returns the quotient of a and b.

        Args:
            a (float): The numerator.
            b (float): The denominator.

        Raises:
            ValueError: If b is zero.

        Returns:
            float: The quotient of a and b.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b