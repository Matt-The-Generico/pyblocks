# devlog #1

  started with the idea of making a 3d, voxel based world and started making it with python (using pyglet and opengl). there's some kind of crash that i can't solve.

  ```
Traceback (most recent call last):
  File "C:\Users\myusername\Desktop\pyblocks1.py", line 509, in <module>
    pyglet.app.run()
    ~~~~~~~~~~~~~~^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\app\__init__.py", line 79, in run
    event_loop.run(interval)
    ~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\app\base.py", line 164, in run
    timeout = self.idle()
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\app\base.py", line 232, in idle
    self.clock.call_scheduled_functions(dt)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\clock.py", line 217, in call_scheduled_functions
    item.func(now - item.last_ts, *item.args, **item.kwargs)
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\app\base.py", line 113, in _redraw_windows
    window.draw(dt)
    ~~~~~~~~~~~^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\window\__init__.py", line 711, in draw
    self.dispatch_event('on_draw')
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\window\__init__.py", line 685, in dispatch_event
    super().dispatch_event(*args)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyglet\event.py", line 371, in dispatch_event
    if getattr(self, event_type)(*args):
       ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\myusername\Desktop\pyblocks1.py", line 464, in on_draw
    self.set_3d()
    ~~~~~~~~~~~^^
  File "C:\Users\myusername\Desktop\pyblocks1.py", line 438, in set_3d
    glMatrixMode(GL_PROJECTION)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "C:\Users\myusername\AppData\Local\Programs\Python\Python313\Lib\site-packages\OpenGL\platform\baseplatform.py", line 487, in __call__
    return self(*args, **named)
  File "src/errorchecker.pyx", line 59, in OpenGL_accelerate.errorchecker._ErrorChecker.glCheckError
OpenGL.error.GLError: GLError(
        err = 1282,
        description = b'opera\xe7\xe3o inv\xe1lida',
        baseOperation = glMatrixMode,
        cArguments = (GL_PROJECTION,)
)
```

what the hell? i just can't solve it.

hours later: i solved it, but now i can't see anything (black screen in the game window), and the ``on_draw`` function isn't inside the correct class. SO WHAT THE FREAK? bro opengl is so difficult
