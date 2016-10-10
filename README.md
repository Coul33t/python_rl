# python_rl
Python roguelike, made with the [tdl](https://pythonhosted.org/tdl/) library. [tdl](https://pythonhosted.org/tdl/) is an awesome wrapper around the awesome [libtcod](http://roguecentral.org/doryen/data/libtcod/doc/1.5.1/index2.html) library.

Be careful : I modified a file in the tdl library (`__init__.py`), so that I can pass the `fgalpha` and `bgalpha` parameters to the `blit` function. (added `fgalpha=1.0, bgalpha=1.0` to the method parameters l.569, and commented l.599 and l.600).

If you really wanna use my code, I advise you to re-merge the `entity_console` and `map_console`. Why did I split the two ? Because I wanted to achieve transparency, which is sadly not available in `libtcod`. I kept the separation for the sake of code clarity (which is pretty ironic, considering that the whole code is in one big file).
