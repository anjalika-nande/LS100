
dot_motion_shader = [
    """ #version 140

        uniform sampler2D p3d_Texture0;
        uniform mat4 p3d_ModelViewProjectionMatrix;

        in vec4 p3d_Vertex;
        in vec2 p3d_MultiTexCoord0;

        out vec4 color;

        void main(void) {
            vec4 newvertex;
            float dot_i;
            float dot_scale = 0.01;
            float dot_x, dot_y, dot_color;
            float maxi = 10000.0;
            vec4 dot_properties;

            dot_i = float(p3d_Vertex[1]);
            dot_properties = texture2D(p3d_Texture0, vec2(dot_i/maxi, 0.0));

            dot_x = dot_properties[2];
            dot_y = dot_properties[1];
            dot_color = dot_properties[0];

            newvertex = p3d_Vertex;

            if (dot_x*dot_x + dot_y*dot_y > 1.0*1.0 || dot_i > 1200) { // only plot 1200 dots inside the circle
                newvertex[0] = 0.0;
                newvertex[1] = 0.0;
                newvertex[2] = 0.0;
            } else {
                newvertex[0] = p3d_Vertex[0]*dot_scale+dot_x;
                newvertex[1] = 0;
                newvertex[2] = p3d_Vertex[2]*dot_scale+dot_y;
            }

            color = vec4(dot_color, dot_color, dot_color, 1.0);

            gl_Position = p3d_ModelViewProjectionMatrix * newvertex;
        }
    """,

    """ #version 140
        in vec4 color;
        out vec4 gl_FragColor;

        void main() {
            gl_FragColor = color;
        }

    """
]

if __name__ == "__main__":
    import sys
    import numpy as np
    import os

    sys.path.append(r"C:\Users\Max\Desktop\LS100\modules")

    from shared import Shared
    import socket

    stimuli = []
    t_stimuli = []

    coherences = [0, 25, 50, 100]
    directions = [-1, 1] # left, right
    number_fish = 2
    for direction in directions:
        for coherence in coherences:
            stimuli.append([direction, coherence])
            t_stimuli.append(20) #  5s 0% coherence, 10s coherence level, 5s 0%

    shared = Shared(r'C:\LS100\LS100_free_swimming_4fish_data', "dot_motion_coherence_new", stimuli=stimuli, t_stimuli=t_stimuli, shaders=[dot_motion_shader], python_file = __file__)

    shared.start_threads()

    from scene import Scene
    from panda3d.core import *

    class World(Scene):

        def __init__(self):

            # Init the scene
            Scene.__init__(self, shared=shared)

            self.background_circle = dict({})
            self.circles = dict({})
            self.dummytex = dict({})

            self.dots_position = dict({})
            self.dots_x = dict({})
            self.dots_y = dict({})

            self.t_ = [0, 0, 0, 0]

            for fish_index in range(number_fish):

                self.background_circle[fish_index] = self.create_circles(1, edges=30)
                self.background_circle[fish_index].reparentTo(self.fish_nodes[fish_index])

                self.background_circle[fish_index].setScale(1, 0, 1)
                self.background_circle[fish_index].setColor(0,0, 0)
                self.background_circle[fish_index].setPos(0, 0.001, 0)

                filepath = os.path.join(os.path.split(__file__)[0], "circles.bam")
                self.circles[fish_index] = self.loader.loadModel(Filename.fromOsSpecific(filepath))
                self.circles[fish_index].reparentTo(self.fish_nodes[fish_index])

                self.dummytex[fish_index] = Texture("dummy texture")
                self.dummytex[fish_index].setup2dTexture(10000, 1, Texture.T_float, Texture.FRgb32)
                self.dummytex[fish_index].setMagfilter(Texture.FTNearest)

                ts1 = TextureStage("part2")
                ts1.setSort(-100)

                self.circles[fish_index].setTexture(ts1, self.dummytex[fish_index])
                self.circles[fish_index].setShader(self.compiled_shaders[0])

                self.dots_x[fish_index] = 2 * np.random.random(10000).astype(np.float32) - 1
                self.dots_y[fish_index] = 2 * np.random.random(10000).astype(np.float32) - 1

                self.dots_position[fish_index] = np.empty((1, 10000, 3)).astype(np.float32)
                self.dots_position[fish_index][0, :, 0] = self.dots_x[fish_index]
                self.dots_position[fish_index][0, :, 1] = self.dots_y[fish_index]
                self.dots_position[fish_index][0, :, 2] = np.random.randint(0, 3,10000).astype(np.float32) * 0 + 1  # 0 will be black, 1, will be white, 2 will be hidden

                memoryview(self.dummytex[fish_index].modify_ram_image())[:] = self.dots_position[fish_index].tobytes()

        def stimulus(self, fish_index, i_stimulus, t_stimulus, frame, time, dt, trial):

            direction, coherence = stimuli[i_stimulus]

            if self.t_[fish_index] >= 0.025: # update every 50 ms
                speed = 0.025
                coherence = 50
                direction = -1
                if fish_index == 3:
                    print(direction)

                random_vector = np.random.randint(100, size=10000)
                if 5 <= time < 15:
                    coherent_change_vector_ind = np.where(random_vector < coherence)  # this fraction moves coherently
                    coherent_random_vector_ind = np.where(random_vector >= coherence)  # this fraction moves randomly
                else:
                    coherent_change_vector_ind = np.where(random_vector < 0)  # this fraction moves coherently
                    coherent_random_vector_ind = np.where(random_vector >= 0)  # this fraction moves randomly

                if direction == -1: # to right
                    ang = 90

                if direction == 1: # to left
                    ang = -90

                dx1 = np.cos((self.shared.current_fish_accumulated_orientation_lowpass[fish_index].value + ang) * np.pi / 180.)
                dy1 = np.sin((self.shared.current_fish_accumulated_orientation_lowpass[fish_index].value + ang) * np.pi / 180.)

                rand_ang = np.random.random(len(coherent_random_vector_ind[0]))*360
                dx2 = np.cos((self.shared.current_fish_accumulated_orientation_lowpass[fish_index].value + rand_ang) * np.pi / 180.)
                dy2 = np.sin((self.shared.current_fish_accumulated_orientation_lowpass[fish_index].value + rand_ang) * np.pi / 180.)

                self.dots_x[fish_index][coherent_change_vector_ind] -= dx1 * speed
                self.dots_y[fish_index][coherent_change_vector_ind] -= dy1 * speed

                #self.dots_x[fish_index][coherent_random_vector_ind] -= dx2 * speed
                #self.dots_y[fish_index][coherent_random_vector_ind] -= dy2 * speed

                self.dots_x[fish_index][coherent_random_vector_ind] = 2 * np.random.random(len(coherent_random_vector_ind[0])).astype(np.float32) - 1
                self.dots_y[fish_index][coherent_random_vector_ind] = 2 * np.random.random(len(coherent_random_vector_ind[0])).astype(np.float32) - 1

                # Wrap them
                self.dots_x[fish_index] = (self.dots_x[fish_index] + 1) % 2 - 1
                self.dots_y[fish_index] = (self.dots_y[fish_index] + 1) % 2 - 1

                self.dots_position[fish_index][0, :, 0] = self.dots_x[fish_index]
                self.dots_position[fish_index][0, :, 1] = self.dots_y[fish_index]

                self.t_[fish_index] = 0
            else:
                self.t_[fish_index] += dt

            memoryview(self.dummytex[fish_index].modify_ram_image())[:] = self.dots_position[fish_index].tobytes()

    try:
        world = World()
        world.run()
    except:
        shared.error("scene_error.txt", sys.exc_info())
