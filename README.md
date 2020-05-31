# coro-scratch
A Scratch 2.0 to Python transpiler that makes extensive use of coroutines

coro-scratch is a simple command line tool that can convert Scratch projects to .py source files that can be run in any Python version greater than or equal to 3.4. It makes extensive use of asyncio and coroutines in the transpiled files.

# What versions of Scratch does this work with?
coro-scratch only works with Scratch 2.0 projects as the file formats for 1.4 and 3.0 are very different. Adding support for Scratch 3.0 projects would not be very difficult, but I do not have any plans to do so at the moment. If anyone wants to add it fork this repo and send a PR. :)

# How does it work?
A longstanding problem with transpiling Scratch projects to other languages is how to deal with its concurenncy model. The transpiled programs can't use threads because the scripts in a Scratch project only yield at specific places, while threads can yield at any time. Since most programming languages only have threads (or multiple processes, which would be even less suitable) for managing concurenncy, this has meant that most Scratch to X "transpilers" really just embed an interpreter and a project together. coro-scratch gets around this by using coroutines, which are like normal subroutines, but they can be "paused" and "unpaused" at specific points. This allows the transpiled code to yield just like Scratch would.

# How complete is this?
coro-scratch is supports quite a few blocks, including most of the blocks in Operators, Data, and Control. It supports a few Events, Sensing, and Looks blocks. It has full support for custom blocks. Check out the [example projects](https://scratch.mit.edu/users/coro-scratch) for the full details.

coro-scratch has support for multiple sprites and scripts running at the same time. E.G two sprites with two green flag scripts each.

Also, the programs created by coro-scratch are CLI only, no graphics or sound blocks will be supported any time soon (except for say for, which just prints to the console.)

# Usage
Clone this repo, and run `python3 convert.py infile.sb2 outfile.py`

The generated programs must be run on Python3.4+

# License
coro-scratch is released under the MIT license, see LICENSE.txt for details.
