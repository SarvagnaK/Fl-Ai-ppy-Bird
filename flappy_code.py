import random
import sys
import pygame
from pygame.locals import *
import numpy
import matplotlib.pyplot as plt

# Screen width and height
SW = 280
SH = 511

# Base Y coordinate 
BASEY = SH * 0.8
# Dictionary to hold images
IMAGES = {}
# Initialize pygame font
pygame.font.init()
# Create a pygame window
WINDOW = pygame.display.set_mode((SW, SH))
# Set the font for displaying text
Font = pygame.font.SysFont("Arial Black", 20)
# Paths to images
BIRD = 'imgs/bird1.png'
BG = 'imgs/bg.png'
PIPE = 'imgs/pipe.png'
# Initialize Q-values for states and actions
Q = numpy.zeros((15, 25, 2), dtype=float)
# Frames per second
FPS = 60 

def static():
    # Initial position of the bird
    birdxpos = int(SW / 5)
    birdypos = int(SH  / 2)
    basex = 0
    while (True):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == KEYDOWN and (event.key == K_RETURN ):
                return
            else:
                # Blit images onto the window
                WINDOW.blit(IMAGES['background'], (0, 0))
                WINDOW.blit(IMAGES['bird'], (birdxpos, birdypos))
                WINDOW.blit(IMAGES['base'], (basex, BASEY))

                start_message = Font.render("Press Enter", 1, (255, 255, 255))
                WINDOW.blit(start_message, (SW/3.5,SH-30))


                pygame.display.update()
                FPSCLOCK.tick(FPS)

def game_start(generation, x, y):
    score = 0
    birdxpos = int(SW / 5)
    birdypos = int(SH / 2)
    basex1 = 0
    basex2 = SW

    bgx1 = 0
    bgx2 = IMAGES['background'].get_width()

    # Get new pipes
    newPipe1 = get_new_pipe()
    newPipe2 = get_new_pipe()

    # Upper pipes list
    up_pipes = [
        {'x': SW + 200, 'y': newPipe1[0]['y']},
        {'x': SW + 500, 'y': newPipe2[0]['y']}
    ]

    # Bottom pipes list
    bttm_pipes = [
        {'x': SW + 200, 'y': newPipe1[1]['y']},
        {'x': SW + 500, 'y': newPipe2[1]['y']}
    ]

    # Pipe velocity
    pipeVelx = -4  

    # Bird's initial velocity and acceleration
    birdyvel = -9
    birdymaxvel = 10
    birdyvelmin = -8
    birdyacc = 1

    # Bird's flap acceleration
    playerFlapAccv = -8
    playerFlapped = False

    while (True):
        # Convert bird position to discrete state
        x_prev, y_prev = convert(birdxpos, birdypos, bttm_pipes)
        # AI decides whether to jump or not
        jump = ai_play(x_prev, y_prev)

        for event in pygame.event.get():
            if event.type == QUIT:
                
                pygame.quit()
                sys.exit()

        if jump:
            if birdypos > 0:
                birdyvel = playerFlapAccv
                playerFlapped = True

        playerMidPos = birdxpos + IMAGES['bird'].get_width() / 2
        for pipe in up_pipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1

        # this is for gravity mechanics
        if birdyvel < birdymaxvel and not playerFlapped:
            birdyvel += birdyacc

# this to ensure that sudden upward movement is applied only once.
        if playerFlapped:
            playerFlapped = False

        
        playerHeight = IMAGES['bird'].get_height()

        # this ensures that based on curret veclocity the bird do not go below base of screen
        birdypos = birdypos + min(birdyvel, BASEY - birdypos - playerHeight)


        # moving of pipes towards left side 
        for upperPipe, lowerPipe in zip(up_pipes, bttm_pipes):
            upperPipe['x'] += pipeVelx
            lowerPipe['x'] += pipeVelx

            # generating new pipes whenever last pipe is close to edge of screen
        if (0 < up_pipes[0]['x'] < 5):
            newPipe = get_new_pipe()
            up_pipes.append(newPipe[0])
            bttm_pipes.append(newPipe[1])

        # if the coordinate of upper pipe moves out of the screen
        if (up_pipes[0]['x'] < -IMAGES['pipe'][0].get_width()):
            up_pipes.pop(0)
            bttm_pipes.pop(0)
        basex1 -= 4 # scrolling of base 
        basex2 -= 4   
        if (basex1 <= -IMAGES['base'].get_width()):
            basex1 = basex2
            basex2 = basex1 + IMAGES['base'].get_width()

        bgx1 -= 2 # scrolling of background 
        bgx2 -= 2  
        if (bgx1 <= -IMAGES['background'].get_width()):
            bgx1 = bgx2
            bgx2 = bgx1 + IMAGES['background'].get_width()

        # Check for collisions
        crashTest = Collision(birdxpos, birdypos, up_pipes, bttm_pipes)
        x_new, y_new = convert(birdxpos, birdypos, bttm_pipes)
        if crashTest:
            reward = -1000
            Q_update(x_prev, y_prev, jump, reward, x_new, y_new)
            return score

        reward = 15
        Q_update(x_prev, y_prev, jump, reward, x_new, y_new)

        # show images and score onto the window
        WINDOW.blit(IMAGES['background'], (bgx1, 0))
        WINDOW.blit(IMAGES['background'], (bgx2, 0))
        for upperPipe, lowerPipe in zip(up_pipes, bttm_pipes):
            WINDOW.blit(IMAGES['pipe'][0], (upperPipe['x'], upperPipe['y']))
            WINDOW.blit(IMAGES['pipe'][1], (lowerPipe['x'], lowerPipe['y']))
        WINDOW.blit(IMAGES['base'], (basex1, BASEY))
        WINDOW.blit(IMAGES['base'], (basex2, BASEY))
        text1 = Font.render("Score:" + str(score), 1, (0, 0, 0))
        text2 = Font.render("Generation:"+ str(generation), 1, (0, 0, 0))
        WINDOW.blit(text1, (SW -  text1.get_width() -10 , 0))
        WINDOW.blit(text2, (0, 0))
        WINDOW.blit(IMAGES['bird'], (birdxpos, birdypos))

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def Collision(birdxpos, birdypos, up_pipes, bttm_pipes):
    # first part is checking of collision with ground and second part < 0 means collision with ceiling 
    if (birdypos >= BASEY - IMAGES['bird'].get_height() or birdypos < 0):
        return True
    for pipe in up_pipes:
        # horizontal and vertical overlap
        pipeHeight = IMAGES['pipe'][0].get_height()
        if (birdypos < pipeHeight + pipe['y'] and abs(birdxpos - pipe['x']) < IMAGES['pipe'][0].get_width()):
            return True

    for pipe in bttm_pipes:
        if (birdypos + IMAGES['bird'].get_height() > pipe['y'] and abs(birdxpos - pipe['x']) < IMAGES['pipe'][0].get_width()):
            return True
    return False

def get_new_pipe():
    pipeHeight = IMAGES['pipe'][1].get_height()
    gap = int(SH / 4)

    # lower pipe should remain above base and should leave some gap for upper pipe
    y2 = int(gap + random.randrange(60, int(SH - IMAGES['base'].get_height() - 1.2 * gap)))                                                

    
    pipex = int(SW + 300)

    y1 = int(y2 - pipeHeight - gap)#upper pipe's y cordinate

    pipe = [
        {'x': pipex, 'y': y1},
        {'x': pipex, 'y': y2}
    ]
    return pipe

def ai_play(x, y):
    max = 0
    jump = False

    if (Q[x][y][1] > Q[x][y][0]):
        max = Q[x][y][1]
        jump = True

    return jump

def convert(birdxpos, birdypos, bttm_pipes):
# Continuous values (like pixel positions) lead to an infinite number of possible states,
#  making the Q-table impractical to store and update.


    x = min(300, bttm_pipes[0]['x'])
    y = bttm_pipes[0]['y'] - birdypos
    if (y < 0):
        y = abs(y) + 408
    return int(x / 40), int(y / 40)

def Q_update(x_prev, y_prev, jump, reward, x_new, y_new):
    if jump:
        Q[x_prev][y_prev][1] = 0.4 * Q[x_prev][y_prev][1] + (0.6) * (reward + max(Q[x_new][y_new][0], Q[x_new][y_new][1]))
    else:
        Q[x_prev][y_prev][0] = 0.4 * Q[x_prev][y_prev][0] + (0.6) * (reward + max(Q[x_new][y_new][0], Q[x_new][y_new][1]))

if __name__ == "__main__":
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_caption("Fl-ai-ppy Bird")

    # Load images
    IMAGES['base'] = pygame.image.load('imgs/base.png').convert_alpha()
    IMAGES['pipe'] = (pygame.transform.rotate(pygame.image.load(PIPE).convert_alpha(), 180), pygame.image.load(PIPE).convert_alpha())
    IMAGES['background'] = pygame.image.load(BG).convert()
    IMAGES['bird'] = pygame.image.load(BIRD).convert_alpha()
    
    generation = 1
    static()
    x = []
    y = []
    while(True):
        # Start the game and get the score
        score = game_start(generation, x, y)
        if score == -1:
            break
        x.append(generation)
        y.append(score)
        generation += 1

    print(generation)
