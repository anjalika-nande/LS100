###########
fish_index = 0
user_prefix = 'LS100_' ##!!

###########

# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import sys
    import numpy as np

    from multiprocessing import Value, Array, Queue
    from panda3d.core import TrueClock

    TrueClock.getGlobalPtr().setCpuAffinity(0xFFFFFFFF)

    from camera_alignment_gui import GUI_Process

    gui = GUI_Process(fish_index)
    gui.start()

    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import *
    import numpy as np
    import sys
    import time
    import os
    import pickle
    import socket


    class World(ShowBase):

        def __init__(self, fish_index):

            loadPrcFileData("",
                            """fullscreen 0
                               win-origin 2692 205
                               undecorated 1
                               win-size 980 980
                               sync-video 0
                               load-display pandagl""")

            # fish_index 0
            # win - origin 2692 205
            # win - size 980 980

            # fish_index 1
            # win - origin 3928 127
            # win - size 1030 1030

            # Init the scene
            ShowBase.__init__(self)
            self.disableMouse()

            [self.k_x, self.k_y, self.k_z, self.k_r] = 0, 0, 1, 90

            computer_name = socket.gethostname()
            self.setup_ID = 0
            if computer_name == "NW152-beh-2":
                self.setup_ID = 0

            # if computer_name == "NW152-beh-2":
            #     self.setup_ID = 1

            if self.setup_ID == 0:
                self.root_path =  r"C:\LS100\{}free_swimming_4fish_data".format(user_prefix)

            # if self.setup_ID == 1:
            #     self.root_path = r"C:\LS100\{}free_swimming_4fish_data".format(user_prefix)

            self.fish_index = fish_index

            try:
                [self.k_x, self.k_y, self.k_z, self.k_r] = pickle.load(
                    open(os.path.join(self.root_path, "stimulus_configuration_fish%d.dat" % self.fish_index), 'rb'))
                print(os.path.join(self.root_path, "stimulus_configuration_fish%d.dat" % self.fish_index))
            except:
                pass

            self.accept("arrow_up", self.up)
            self.accept("arrow_up-repeat", self.up)

            self.accept("arrow_down", self.down)
            self.accept("arrow_down-repeat", self.down)

            self.accept("arrow_right", self.right)
            self.accept("arrow_right-repeat", self.right)

            self.accept("arrow_left", self.left)
            self.accept("arrow_left-repeat", self.left)

            self.accept("z", self.zoom_in)
            self.accept("z-repeat", self.zoom_in)

            self.accept("x", self.zoom_out)
            self.accept("x-repeat", self.zoom_out)

            self.accept("r", self.rotate_right)
            self.accept("r-repeat", self.rotate_right)

            self.accept("t", self.rotate_left)
            self.accept("t-repeat", self.rotate_left)

            self.lens1 = PerspectiveLens()
            self.lens1.setFov(90, 90)
            self.lens1.setNearFar(0.001, 1000)
            self.lens1.setAspectRatio(500. / 550)
            self.cam.node().setLens(self.lens1)

            self.setBackgroundColor(0, 0, 0, 1)

            self.fish_node = self.render.attachNewNode("fish_node")

            self.background_circle1 = self.create_circles(1, edges=30)
            self.background_circle1.reparentTo(self.fish_node)

            self.background_circle2 = self.create_circles(1, edges=30)
            self.background_circle2.reparentTo(self.fish_node)

            # make a cross
            cm = CardMaker('card')

            card0 = self.fish_node.attachNewNode(cm.generate())
            card0.setScale(0.01, 1, 1)
            card0.setPos(-0.005, -0.002, -0.5)
            card0.setColor(1, 1, 1)

            card1 = self.fish_node.attachNewNode(cm.generate())
            card1.setScale(1, 1, 0.01)
            card1.setPos(-0.5, -0.002, -0.005)
            card1.setColor(1, 1, 1)

            card2 = self.fish_node.attachNewNode(cm.generate())
            card2.setScale(0.1, 1, 0.1)
            card2.setPos(0.1 - 0.05, -0.002, 0.1 - 0.05)
            card2.setColor(1, 0, 0)


            self.background_circle1.setScale(1.01, 1.01, 1.01) #1.01, 1.01, 1.01
            self.background_circle1.setColor(1, 0, 1)
            self.background_circle1.setPos(0.0, 0.0, 0)

            self.background_circle2.setScale(0.99, 0.99, 0.99)
            self.background_circle2.setColor(0.0, 0.0, 0.0)
            self.background_circle2.setPos(0, -0.001, 0)

            self.taskMgr.add(self.check_finish, "check_finish")

            self.update()

        def update(self):

            self.fish_node.setPos(self.k_x, 1, self.k_y)
            self.fish_node.setScale(self.k_z, 1, self.k_z)
            self.fish_node.setHpr(0, 0, self.k_r)

            print(self.k_x, self.k_y, self.k_z, self.k_r)

        def rotate_right(self):
            self.k_r += 0.05
            self.update()

        def rotate_left(self):
            self.k_r -= 0.05
            self.update()

        def up(self):
            self.k_x += 0.002
            self.update()

        def down(self):
            self.k_x -= 0.002
            self.update()

        def left(self):
            self.k_y += 0.002
            self.update()

        def right(self):
            self.k_y -= 0.002
            self.update()

        def zoom_in(self):
            self.k_z += 0.002

            self.update()

        def zoom_out(self):
            self.k_z -= 0.002

            self.update()

        def check_finish(self, task):
            if gui.running.value == 1:
                return task.cont
            else:
                pickle.dump([self.k_x, self.k_y, self.k_z, self.k_r],
                            open(os.path.join(self.root_path, "stimulus_configuration_fish%d.dat" % self.fish_index),
                                 'wb'))

                sys.exit()

                return task.done

        def create_circles(self, n, edges=20):

            vdata = GeomVertexData('name', GeomVertexFormat.getV3t2(), Geom.UHStatic)

            prim_wall = GeomTriangles(Geom.UHStatic)

            vertex_writer = GeomVertexWriter(vdata, 'vertex')
            texcoord_writer = GeomVertexWriter(vdata, 'texcoord')

            angs = np.linspace(0, 360, edges)

            for i in range(n):
                for j in range(len(angs)):
                    ang0 = angs[j]
                    ang1 = angs[(j + 1) % edges]
                    vertex_writer.addData3f(0, i, 0)  # stack them in distance
                    vertex_writer.addData3f(np.cos(ang0 * np.pi / 180), i, np.sin(ang0 * np.pi / 180))
                    vertex_writer.addData3f(np.cos(ang1 * np.pi / 180), i, np.sin(ang1 * np.pi / 180))

                    texcoord_writer.addData2f(i / float(n), 0)
                    texcoord_writer.addData2f(i / float(n), 0.5)
                    texcoord_writer.addData2f(i / float(n), 1)

                prim_wall.addConsecutiveVertices(i * edges * 3, edges * 3)
                prim_wall.closePrimitive()

            geom_wall = Geom(vdata)
            geom_wall.addPrimitive(prim_wall)

            circles = GeomNode('card')
            circles.addGeom(geom_wall)

            return NodePath(circles)


    world = World(fish_index)
    world.run()
