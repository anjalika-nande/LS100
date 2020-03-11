# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import sys

    from direct.showbase.ShowBase import ShowBase
    from pandac.PandaModules import *

    class World(ShowBase):

        def __init__(self):

            loadPrcFileData("",
                    """fullscreen 0
                       win-origin 1920 0
                       undecorated 1
                       win-size 5760 1080
                       sync-video 0
                       load-display pandagl""")

            # Init the scene
            ShowBase.__init__(self)
            self.disableMouse()

            self.accept("escape", self.finish)

            self.setBackgroundColor(1, 1, 1, 1)

        def finish(self):

            sys.exit()


    world = World()
    world.run()
