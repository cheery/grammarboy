# Grammarboy

This is a parser engine, written in python, based on CYK algorithm.

Intention was to create a system to build up parsers that are able to guide the user towards correct syntax. I meant to create a tool that gives hint on how to complete the input.

Unfortunately that kind of completion feature turned out to be quite hard to implement overall. Didn't get there. But I got somewhere. Here's a terminal output from a session where I ran the demo.py:

    cheery@ruttunen:~/grammarboy$ python3 demo.py 
    > www.boxbase.org
      |-|'|-----|'|-|

    > +
      '
      expr90 := <expr90> + <term>              # addition                      

    > -
      '
      expr90 := <expr90> - <term>              # subtract                      

    > or
      ||
        expr := <expr90> or <expr>             # logical or                    

    > 50 or 2
    50
    > 50 and 2
    2
    > 20 30
      || ||
        expr := <expr90> or <expr>             # logical or                    
        expr := <expr90> and <expr>            # logical and                   
      expr90 := <expr90> + <term>              # addition                      
      expr90 := <expr90> - <term>              # subtract                      
        stmt := return <expr>                  # return from function          

    > 20 30 5000
      || || |--|
        expr := <expr90> or <expr>             # logical or                    
        expr := <expr90> and <expr>            # logical and                   
      expr90 := <expr90> + <term>              # addition                      
      expr90 := <expr90> - <term>              # subtract                      
        stmt := return <expr>                  # return from function          

    > 50 - 2
    48
    > 50 - 2 or 1
    48
    > 50 - 2 or 1 and 4
    48
    > 0 or 1 and 4
    4
    > 0 or 1 and
      '      |-|
        expr := <expr90> and <expr>            # logical and                   
        expr := <expr90> or <expr>             # logical or                    
        stmt := return <expr>                  # return from function          

    >

Unfortunately I didn't add documentation here, but the source should be easy enough to read through. Beware of bugs and other issues.

If I might happen to return on writing parser engines that provide feedback to the user, I will reuse this repository.
