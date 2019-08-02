# Coizscript

Coizscript is a programming language I developed to learn how to create interpreters. This project is heavily based off of [Crafting Interpreters](https://craftinginterpreters.com/) and [Let's Build a Simple Interpreter!](https://ruslanspivak.com/lsbasi-part1/).

Examples of code can be found in the scripts and lib directories.

## Usage

After cloning the repo, run `csi.py` (short for Coizscript interpreter), along with the location of the file you wish to run as an argument, if you wish. Otherwise, `csi.py` will open up a shell in which you can execute commands.

## Syntax

### Comments

```
// Line comments.

/* Multi-line
   comments */
```

### Arithmetic

+, -, *, /, and % work as in most languages. It worth noting that / is not integer division:

```
print(5 + 2); // result is 7
print(5 - 2); // result is 3
print(5 * 2); // result is 10
print(5 / 2); // result is 2.5
print(5 % 2); // result is 1
```

Precedence works as expected. `()` > `*, /, %` > `+, -`:

```
print(2 + 3 * 4); // result is 14
print((2 + 3) * 4); // result is 20
```

### Variables

Variables are initialized with the `var` keyword. Variables must be initialized before they can be used.

```
var x = 5;
print(x); // result is 5
x = 2;
print(x); // result is 2
// y = 2; // syntax error
var y = x + 2; // y is 4
```

You can also use `x += 1` as a shorthand for `x = x + 1`, and similarly for the other arithmetic operators:

```
var x = 5;
x += 1; // x is 6
x -= 2; // x is 4
x *= 4; // x is 16
x /= 10; // x is 1.6
```

### Conditional and Flow Statements:

`if/else` works similar to C, Java, and similar languages:

```
// Program will print "x not 5.".
var x = 4;

if(x == 5) {
    print("x is 4.");
} else {
    print("x not 5.");
};

```

Conditional statements can use the following symbols:

```
==  // equals
!=  // not equals
>   // greater than
<   // less than
>=  // greater than or equal to
<=  // less than or equal to
or
and
```

Note that the `if/else` block ends with a `;`. **All blocks and statements must end with a `;`**.

`while` and `for` loops are also similar to C, Java, and other similar languages:

```
var i = 0;
while(i < 10) {
    print(i);
    i += 1;
};   // Notice the trailing ;

/* or */

for(var i = 0; i < 10; i += 1) {
    print(i);
};   // Notice the trailing ;
```

### Function Declarations and Calls

One can declare and call a function using the following syntax:

```
func add(a, b) {
    return a + b;
};

print(add(3, 5)); // result is 8
```

### Arrays

Arrays can be declared and used as followed:

```
var arr = [2, 4, 6];
print(arr[0]); // result is 2
arr[1] = 5;
print(arr[1]); // result is 5
```

### Print Function

`print()` can be overloaded to work as a `printf()` function call as in C:

```
var i = 10;
print("i is %d.", i); // result is "i is 10."
```

### Import Function

You can import functions and variables from another file using the `import()` function:

```
import("lib/math");

print(factorial(5)); // result is 120
```