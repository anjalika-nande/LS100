# -*- coding: utf-8 -*-
if __name__ == "__main__":

    import sys
    import numpy as np
    import os
    sys.path.append(r"C:\Users\Max\Desktop\LS100\modules")

    from shared import Shared
    from scene import Scene
    from panda3d.core import *
    from direct.task import Task

    # default black bg, black circle
    # circle = True
    # moving = False
    # gray = False
    stimuli = [0]
    t_stimuli = [5 * 60]

    number_fish = 2
    shared = Shared(r'C:\LS100\LS100_free_swimming_4fish_data', "phototaxis", stimuli=stimuli, t_stimuli=t_stimuli,
                    shaders=[], python_file=__file__)
    # shared = Shared(r'D:\hanna_free_swimming_4fish_data', "hanna_phototaxis", stimuli=stimuli, t_stimuli=t_stimuli,
    #               shaders=[dot_motion_shader, phototaxis_shader], python_file=__file__)
    shared.start_threads()


    class World(Scene):

        def __init__(self):

            # Init the scene
            Scene.__init__(self, shared=shared)

            # Place cards on the fishnodes
            cm = CardMaker('card')

            dot_scale = 0.3
            self.dummynodes = []
            self.cardnodes = []
            self.number_fish = 2
            self.background_circle = dict({})
            self.circle = True

            # for fish_index in range(self.number_fish):
            #     self.background_circle[fish_index] = self.create_circles(1, edges=30)
            #     self.background_circle[fish_index].reparentTo(self.fish_nodes[fish_index])
            #
            #     self.background_circle[fish_index].setScale(1, 0, 1)
            #     self.background_circle[fish_index].setColor(0, 0, 0)
            #     self.background_circle[fish_index].setPos(0, 0.001, 0)
            #
            #     filepath = os.path.join(os.path.split(__file__)[0], "circles.bam")
            #     self.circles[fish_index] = self.loader.loadModel(Filename.fromOsSpecific(filepath))
            #     self.circles[fish_index].reparentTo(self.fish_nodes[fish_index])
            #
            #     self.dummytex[fish_index] = Texture("dummy texture")
            #     self.dummytex[fish_index].setup2dTexture(10000, 1, Texture.T_float, Texture.FRgb32)
            #     self.dummytex[fish_index].setMagfilter(Texture.FTNearest)

            for i in range(self.number_fish):

                self.dummynodes.append(self.fish_nodes[i].attachNewNode("Dummy Node"))
                self.cardnodes.append(self.dummynodes[i].attachNewNode(cm.generate()))
                self.cardnodes[i].setScale(dot_scale, 1, dot_scale)
                self.cardnodes[i].setPos(-dot_scale / 2, 0, -dot_scale / 2)

            # if self.circle:
            pic = self.loader.loadTexture("blackwhitepatch.png")
            # elif gray:
            #     pic = self.loader.loadTexture("gray.png")
            # else:
            #     pic = self.loader.loadTexture("black.png")

            pic.setMagfilter(Texture.FTLinear)
            pic.setMinfilter(Texture.FTLinearMipmapLinear)
            pic.setAnisotropicDegree(16)

            for fish_index in range(self.number_fish):
                self.cardnodes[fish_index].setTexture(pic)
                self.cardnodes[fish_index].setTransparency(True)
                self.cardnodes[fish_index].setTexScale(TextureStage.getDefault(), 0.99, 0.99)

            c = 0  # same as 0.5 * 255 in illustrator, rgb, gray
            self.setBackgroundColor(c, c, c, 1)

        def stimulus(self, fish_index, i_stimulus, t_stimulus, frame, time, dt, trial, ang = 0):
            # To Do : Make the stimulus move and add stimulus to the second fish
            for fish_index in range(self.number_fish):
                # default black for bg
                c = 0
                # all gray
                #     if gray:
                #         c = 0.5
                #         self.setBackgroundColor(c, c, c, 1)
                #
                radius_spot = 0.24
                center_spot = 0.45

                x = self.shared.current_fish_position_x[fish_index].value
                y = self.shared.current_fish_position_y[fish_index].value


                #if (x-center_spot)**2 + y**2 <= radius_spot :
                    #self.dummynodes[fish_index].setHpr(np.pi/2, 0, 0)
                    #self.cardnodes[fish_index].setTexRotate(TextureStage.getDefault(), np.pi/2)
                #self.dummynodes[fish_index].setPos(x, 0.0001, y)

                #ang = np.arctan2(self.dummynodes[fish_index].getX(),
                                 #self.dummynodes[fish_index].getZ()) * 180 / np.pi - 90

                # moving stimulus
                # if moving:
                #     # positions = [[1,1],[0.3,0.3],[1,0.6],[0.7,0.3]]
                #     self.cardnodes[fish_index].setTexOffset(TextureStage.getDefault(), time, 0)

        def timedtask(self, task, fish_index):
            if task.time < 10.0:
                return Task.cont

            self.dummynodes[fish_index].setHpr(np.pi / 2, 0,0)
            return Task.done


    try:
        world = World()
        world.run()
    except:
        shared.error("scene_error.txt", sys.exc_info())
