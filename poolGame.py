####################################################################################################################
'''
Student: April Wu 
AndrewID: aprilw
Game: 8 Ball Pool

Implemented Features: 

To-be implemented: 

lines 15-234: Original Code
lines 234-231: From https://github.com/jatinmandav/Gaming-in-Python/blob/master/8_Ball_Pool/8BallPool.py
lines 232-306: Original Code
lines 307-329: Logic from https://longbaonguyen.github.io/courses/apcsa/apjava.html
lines 300-634: Original Code
'''
####################################################################################################################
import pygame, random, math, sys, copy
from pygame.locals import *

pygame.init()
width = 1200 #88in. pool table + 60 margins x 2 = 1000 & 200 more for p1 & p2 standings
height = 560
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("8 Ball Pool")
background = pygame.draw.rect(screen, (255,255,240), (0,0,width,height))
pygame.display.update()
time = pygame.time.Clock()
solidBalls = []
stripeBalls = []
allBalls = pygame.sprite.Group()
cue = pygame.sprite.GroupSingle()
ballBreak = False #when this is true, the game can begin
moves = [] #keeps track of the ballType hit and determines which player goes (mAYBE?!)

class startScreen(object):
	def __init__(self):
		self.image = pygame.image.load("openscreen.png")
		self.rect = self.image.get_rect()
		screen.fill((255,255,255))
		screen.blit(self.image, (0,0))
		pygame.display.flip()
		self.time = pygame.time.Clock()

	def run(self):
		waiting = True
		while waiting:
			self.time.tick(60)
			for event in pygame.event.get():
				if event.type == pygame.KEYDOWN:
					if pygame.key.get_pressed()[pygame.K_SPACE]:
						waiting = False

#NOTE: blit fills the screen with an image the same way pygame.fill fills the screen with a color
def distance(x1,y1,x2,y2):
	dx = (x1-x2)**2
	dy = (y1-y2)**2
	return (dx+dy)**0.5

class Table(object):
	def __init__(self):
		self.length = 880
		self.width = 440 
		self.margin = 60 

	def borderDim(self):
		#returns left --> top --> right --> bottom
		return [(self.margin,self.margin),(self.margin+self.length,self.margin),\
				(self.margin,self.margin + self.width),(self.margin+self.length, self.margin+self.width)]

	def borderLengths(self):
		#distances: top-left --> top right; topR --> bottomR; bottomR --> bottomL; bottomL --> topL 
		d1 = distance(self.margin,self.margin,self.margin,self.width+self.margin*0.8)
		d2 = distance(self.margin,self.width+self.margin*0.8,self.margin,self.margin)
		d3 = distance(self.margin,self.width+self.margin*0.8,width-self.margin,height-self.margin)
		d4 = distance(width-self.margin,height-self.margin,self.margin,self.margin)
		return (d1, d2, d3, d4)

	def drawTable(self):
		#table
		pygame.draw.rect(screen, (10, 108, 3), (self.margin,self.margin,self.length,self.width))
		stringGap = self.length//4
		for i in range(1,4):
			height = self.margin + self.width
			pygame.draw.rect(screen, (192,192,192),(self.margin+stringGap*i,self.margin,self.margin*0.05,self.width))
		#borders: left, top, right, bottom 
		pygame.draw.rect(screen, (54, 37, 20),(self.margin,self.margin,self.margin*0.2,self.width))
		pygame.draw.rect(screen, (54, 37, 20),(self.margin,self.margin,self.length,self.margin*0.2))
		pygame.draw.rect(screen, (54, 37, 20),(self.length+self.margin*0.8,self.margin,self.margin*0.2,self.width))
		pygame.draw.rect(screen, (54, 37, 20),(self.margin,self.width+self.margin*0.8,self.length,self.margin*0.2))

poolTable = Table()

class Pocket(pygame.sprite.Sprite):
	def __init__(self, x, y): #x and y = location of pockets 
		pygame.sprite.Sprite.__init__(self)
		self.length = 50
		self.width = 50
		self.radius = int(self.width*0.4)
		self.color = (59,39,19)
		self.image = pygame.Surface((self.length,self.width)) #the ball is 15x15
		self.image.fill(self.color)
		self.rect = self.image.get_rect() #update rect to update ball pos
		self.rect.center = (int(x), int(y))
		self.rect.centerx = x
		self.rect.centery = y

	def drawPockets(self):
		pygame.draw.circle(screen, self.color, (self.rect.centerx,self.rect.centery), self.radius)
	
#sample pocket object to help with coords
sPocket = Pocket(1,1)
#pocket coords starting from the top-left corner and going clockwise
pocketCoords = [(poolTable.margin+sPocket.radius,poolTable.margin+sPocket.radius), \
				(poolTable.margin+poolTable.length//2,poolTable.margin+sPocket.radius),\
			 	(poolTable.margin+poolTable.length-sPocket.radius,poolTable.margin+sPocket.radius),\
			 	(poolTable.margin+poolTable.length-sPocket.radius,poolTable.margin+poolTable.width-sPocket.radius),\
			 	(poolTable.margin+poolTable.length//2,poolTable.margin+poolTable.width-sPocket.radius),\
			 	(poolTable.margin+sPocket.radius,poolTable.margin+poolTable.width-sPocket.radius)]

pockets = pygame.sprite.Group()
for x in range(6): #the six pockets of the table
	x,y = pocketCoords[x]
	pockets.add(Pocket(x,y))

#detect if the ball is in the pocket --> if true disappear from surface and add to player
def ballInPocket(pocket,ball):
		dist = distance(pocket.rect.centerx, pocket.rect.centery, ball.rect.centerx, ball.rect.centery)
		if dist < pocket.radius + ball.radius:
			allBalls.remove(ball)
			return True
		else:
			return False

class Ball(pygame.sprite.Sprite):
	def __init__(self, x, y, color, num): #x,y the location of the ball (center)
		pygame.sprite.Sprite.__init__(self)
		self.num = num
		self.image = pygame.Surface((15,15)) #the ball is 15x15
		self.color = color
		self.image.fill(self.color)
		self.rect = self.image.get_rect() #update rect to update ball pos
		self.rect.center = (int(x), int(y))
		self.rect.centerx = x
		self.rect.centery = y
		self.radius = 12
		self.mass = 2
		self.vx = 0
		self.vy = 0
		self.force = 0
		self.friction = 0.05
		self.isStripe = False
		self.drawOutline = False

	def drawBall(self, point):
		pygame.draw.circle(screen, self.color, (point), self.radius)
		if self.isStripe: 
			pygame.draw.line(screen, (255,255,255), (self.rect.centerx,self.rect.centery-self.radius), \
							(self.rect.centerx,self.rect.centery+self.radius), 3)
		if self.drawOutline:
			pygame.draw.circle(screen, (119,136,153),(self.rect.centerx,self.rect.centery),self.radius,3)

	#speed changes when ball collides
	def moveBall(self):
		if self.rect.centerx + self.radius >= poolTable.length + poolTable.margin*0.8:
			self.vx *= -1
		elif self.rect.centerx - self.radius <= poolTable.margin*1.2:
			self.vx *= -1
		if self.rect.centery + self.radius >= poolTable.width + poolTable.margin*0.8: 
			self.vy *= -1
		elif self.rect.centery - self.radius <= poolTable.margin*1.2:
			self.vy *= -1
		self.rect.centerx += self.vx
		self.rect.centery += self.vy
	
	#when any ball hits the border change speed	
	def hitBorder(self):
		self.rect.centerx += self.vx
		self.rect.centery += self.vy
		if self.rect.centerx + self.radius >= poolTable.length + poolTable.margin*0.8:
			self.rect.centerx = self.radius + poolTable.length + poolTable.margin*0.3
			self.vx *= -1
		if self.rect.centerx - self.radius <= poolTable.margin*1.2:
			self.rect.centerx = self.radius + poolTable.margin*1.2
			self.vx *= -1
		if self.rect.centery + self.radius > poolTable.width + poolTable.margin*0.8:
			self.rect.centery = poolTable.width + poolTable.margin*0.3 + self.radius
			self.vy *= -1
		if self.rect.centery - self.radius <= poolTable.margin*1.2:
			self.rect.centery = self.radius + poolTable.margin*1.2
			self.vy *= -1
		self.vx -= self.friction
		self.vy -= self.friction
	
	def collided(self, ballSprite):
		if pygame.sprite.collide_circle(self, ballSprite):
			self.moveBall()

class Stick(object):
	def __init__(self):
		self.x, self.y = 0,0 
		self.width = 50
		self.angle = 0
		self.force = 0
		self.dx = 0
		self.dy = 0
		self.ballNum = 0

	#draws the force 
	def showForce(self):
		xPosition = width//2 - poolTable.margin
		yPosition = poolTable.margin*0.5
		font = pygame.font.SysFont("Calibri", 30) 
		text = font.render(f"FORCE: {self.force}", False,  (0,0,0))
		textRect = text.get_rect()
		textRect.centerx = xPosition
		textRect.centery = yPosition
		screen.blit(text, textRect)

	#stick movement from: 
	def drawStick(self,cueBallX, cueBallY):
		self.x, self.y = pygame.mouse.get_pos()
		if (self.x > poolTable.margin and self.x < poolTable.margin + poolTable.length) and \
			(self.y > poolTable.margin and self.y < poolTable.margin + poolTable.width): 
			self.angle = math.atan2((cueBallY - self.y), (cueBallX - self.x))
			self.dx = math.cos(self.angle)
			self.dy = math.sin(self.angle)
			pygame.draw.line(screen, (43, 29, 14), (self.x,self.y), (cueBallX,cueBallY),5)

	#the prediction line
	def drawPredictions(self, cueBallX, cueBallY):
		for b in allBalls:
			if b.num == self.ballNum:
				b.drawOutline = True
				bx, by = b.rect.centerx, b.rect.centery 
				cx, cy = cueBall.rect.centerx, cueBall.rect.centery
				length = distance(bx,by,cx,cy)
				#line that aims directly at target ball
				pointerX = cueBall.rect.centerx + length*self.dx
				pointerY = cueBall.rect.centery + length*self.dy
				addX, addY = 0, 0
				if bx - b.radius < pointerX < bx + b.radius and by - b.radius < pointerY < by + b.radius:
				   	pygame.draw.line(screen, (255,255,255),(pointerX, pointerY), (cueBall.rect.centerx, cueBall.rect.centery),1)
				   	x,y  = ballDestination(b, cueBall)
				   	if by == pointerY:
				   		angle = self.angle 
				   		addX = x * math.cos(angle)
				   		addY = y * math.sin(angle)
				   	elif pointerY < by:
				   		angle = self.angle - math.pi/6
				   		addX = x * math.cos(angle)
				   		addY = y * math.sin(angle)
				   	else:
				   		angle = self.angle + math.pi/6
				   		addX = x * math.cos(angle)
				   		addY = y * math.sin(angle)
				   	predictX = x + addX
				   	predictY = y + addY
				   
				   	if predictX < poolTable.margin:
				   		diff = poolTable.margin-predictX
				   		dx = distance(b.rect.centerx, b.rect.centery, poolTable.margin, b.rect.centery)
				   		dy = math.tan(angle)*dx
				   		d = (dx**2 + dy**2)**0.5
				   		endX = poolTable.margin + abs(diff*math.cos(angle))
				   		endY = poolTable.margin + abs(diff*math.sin(angle))
				   		predictX = poolTable.margin
				   		pygame.draw.line(screen,(255,255,255),(predictX, predictY),(endX,endY))
				   		#pygame.draw.line(screen, (59,39,19),(predictX, predictY),(b.rect.centerx,b.rect.centery),1)
				   
				   	elif predictX > poolTable.margin + poolTable.length:
				   		diff = predictX - (poolTable.margin + poolTable.length)
				   		dx = distance(b.rect.centerx, b.rect.centery, poolTable.margin+poolTable.length, b.rect.centery)
				   		dy = math.tan(angle)*dx
				   		d = (dx**2 + dy**2)**0.5
				   		endX = poolTable.margin + poolTable.length - abs(diff*math.cos(angle))
				   		endY = poolTable.margin + abs(diff*math.sin(angle))
				   		predictX = poolTable.margin + poolTable.length
				   		pygame.draw.line(screen,(255,255,255),(predictX, predictY),(endX,endY))
				   		#pygame.draw.line(screen, (59,39,19),(predictX, predictY),(b.rect.centerx,b.rect.centery),1)
				   
				   	if predictY < poolTable.margin:
				   		diff = poolTable.margin - predictY
				   		dy = distance(b.rect.centerx, b.rect.centery, b.rect.centerx, poolTable.margin)
				   		dx = dy/math.tan(angle)
				   		d = (dx**2 + dy**2)**0.5
				   		endX = poolTable.margin + abs(diff*math.cos(angle))
				   		endY = poolTable.margin + abs(diff*math.sin(angle))
				   		predictY = poolTable.margin
				   		pygame.draw.line(screen,(255,255,255),(predictX, predictY),(endX,endY))
				   		#pygame.draw.line(screen, (59,39,19),(predictX, predictY),(b.rect.centerx,b.rect.centery),1)
				   
				   	elif predictY > poolTable.margin + poolTable.width:
				   		diff = predictY - (poolTable.margin + poolTable.width)
				   		dy = distance(b.rect.centerx, b.rect.centery, b.rect.centerx, poolTable.margin + poolTable.width)
				   		dx = dy/math.tan(angle)
				   		d = (dx**2 + dy**2)**0.5
				   		endX = poolTable.margin + abs(diff*math.cos(angle))
				   		endY = poolTable.margin + poolTable.width + abs(diff*math.sin(angle))
				   		predictY = poolTable.margin + poolTable.width
				   		pygame.draw.line(screen,(255,255,255),(predictX, predictY),(endX,endY*0.5))
				   	pygame.draw.line(screen, (59,39,19),(predictX, predictY),(b.rect.centerx,b.rect.centery),1)

			else:
				b.drawOutline = False

	def shoot(self, force, cueball):
		cueball.vx += force*self.dx
		cueball.vy += force*self.dy
		Ball.hitBorder(cueball)
cueStick = Stick()

#colors are in the order yellow, blue, red, purple, orange, green, brown
colors = [(255, 219, 88),(71,169,255),(255,0,0),(204,204,255),(255,166,33),(156,255,8),(103,77,60)]
number = [1,2,3,4,5,6,7,9,10,11,12,13,14,15]
balls = []
#using sBall Dimensions for ball bRad (bRad) (measurements)
sBall = Ball(10, 10, (0,0,0),16) 

#CITATION: From https://github.com/jatinmandav/Gaming-in-Python/blob/master/8_Ball_Pool/8BallPool.py
w = poolTable.width + poolTable.margin*2
start = int(poolTable.width*0.35)
bRad = sBall.radius
ballLoc =[(start, w//2 - 4*bRad),(start + 2*bRad, w//2 - 3*bRad),(start, w//2 - 2*bRad),\
		  (start + 4*bRad, w//2 - 2*bRad),(start + 2*bRad, w//2 - 1*bRad),(start, w//2),\
		  (start + 6*bRad, w//2 - 1*bRad),(start + 8*bRad, w//2),\
		  (start + 6*bRad, w//2 + 1*bRad),(start + 2*bRad, w//2 + 1*bRad),(start, w//2 + 2*bRad),\
		  (start + 4*bRad, w//2 + 2*bRad),(start + 2*bRad, w//2 + 3*bRad),(start, w//2 + 4*bRad)]

eightBall = Ball(start + 4*bRad, w//2, (0,0,0),8)
cueBall = Ball(poolTable.length * (3/4) + poolTable.margin, poolTable.width*0.5 + poolTable.margin, (255,255,255), 0)

#creating the solid and stripe balls and assigning them locations
bLocCopy = copy.copy(ballLoc)
numSolid = 1
for b in range(7):
	x,y = random.choice(bLocCopy)
	newBall = Ball(x,y, colors[b], numSolid)
	numSolid += 1
	bLocCopy.remove((x,y))
	solidBalls.append(newBall)
	balls.append(newBall)
	allBalls.add(newBall)

numStripe = 9
for b in range(7):
	x,y = random.choice(bLocCopy)
	newBall = Ball(x,y, colors[b], numStripe)
	numStripe += 1
	bLocCopy.remove((x,y))
	newBall.isStripe = True
	stripeBalls.append(newBall)
	balls.append(newBall)
	allBalls.add(newBall)

balls.append(eightBall)
allBalls.add(eightBall)
cue.add(cueBall)

#filling the balls with a location
while len(bLocCopy) > 0:
	for b in range(len(balls)):
		ball = balls[b]
		location = random.choice(bLocCopy)
		ball.x, ball.y = location
		bLocCopy.remove(location)

#CITATION: logic inspired from: https://longbaonguyen.github.io/courses/apcsa/apjava.html
def ballCollide(ball1, ball2):
	dx = abs(ball1.rect.centerx - ball2.rect.centerx)
	dy = abs(ball1.rect.centery - ball2.rect.centery)
	angle = math.atan2(dy,dx)
	cosine = math.cos(angle)
	sine = math.sin(angle)
	vx1 = cosine*ball1.vx + sine*ball1.vy
	vy1 = -1*sine*ball1.vx + cosine*ball1.vy 
	vx2 = cosine*ball2.vx + sine*ball2.vy
	vy2 = -1*sine*ball2.vx + cosine*ball2.vy 
	tempVX1, tempVX2 = 0, 0
	tempVX1 = ((ball1.mass-ball2.mass)*ball1.vx + 2*ball2.mass*ball2.vx)/(ball1.mass+ball2.mass)
	tempVX2 = (2*ball1.mass*ball1.vx + (ball2.mass-ball1.mass)*ball2.vx)/(ball1.mass+ball2.mass)
	print(tempVX1, tempVX2)
	ball1.vx = cosine*tempVX1 - sine*vy1
	ball1.vy = sine*tempVX1 + cosine*vy1
	ball2.vx = cosine*tempVX2 - sine*vy2
	ball2.vy = sine*tempVX2 + cosine*vy2
	ball1.moveBall()
	ball2.moveBall()
	overlap = ball1.radius + ball2.radius - distance(ball1.rect.x, ball1.rect.y, ball2.rect.x, ball2.rect.y)
	ball1.rect.centerx += overlap*1.5
	ball2.rect.centerx -= overlap*1.5

#draws the prediction line
def ballDestination(ball, cueBall):
	dx = abs(ball.rect.centerx - cueBall.rect.centerx)
	dy = abs(ball.rect.centery - cueBall.rect.centery)
	angle = math.atan2(dy,dx)
	cosine = math.cos(angle)
	sine = math.sin(angle)
	vx1 = cosine*ball.vx + sine*ball.vy
	vy1 = -1*sine*ball.vx + cosine*ball.vy 
	vx2 = cosine*cueBall.vx + sine*cueBall.vy
	vy2 = -1*sine*cueBall.vx + cosine*cueBall.vy 
	tempVX1, tempVX2 = 0, 0
	tempVX1 = ((ball.mass-cueBall.mass)*ball.vx + 2*cueBall.mass*cueBall.vx)/(ball.mass+cueBall.mass)
	tempVX2 = (2*ball.mass*ball.vx + (cueBall.mass-ball.mass)*cueBall.vx)/(ball.mass+cueBall.mass)
	ball.vx = cosine*tempVX1 - sine*vy1
	ball.vy = sine*tempVX1 + cosine*vy1
	ballDestX = ball.rect.centerx + ball.vx
	ballDestY = ball.rect.centery + ball.vy
	return (ballDestX,ballDestY)

#calculates the angle between ball1 and cueBall
def angleCalculator(ball, item): #item can be ball or stick
	if isinstance(item, Ball):
		dx = (item.rect.centerx - ball.rect.centerx)
		dy = (item.rect.centery - ball.rect.centery)
	elif isinstance(item, Stick):
		dx = (item.x - ball.rect.centerx)
		dy = (item.y - ball.rect.centery)
	return math.atan2(dy,dx)

#using the friction to slow the ball's speed
def slowBall(ball):
	if ball.vx > 0:
		ball.vx -= ball.friction * 2
		if ball.vx < 0.05:
			ball.vx = 0
	elif ball.vx < 0:
		ball.vx += ball.friction * 2
		if ball.vx > -0.05:
			ball.vx = 0
	if ball.vy > 0:
		ball.vy -= ball.friction * 2
		if ball.vy < 0.05:
			ball.vy = 0
	elif ball.vy < 0:
		ball.vy += ball.friction * 2
		if ball.vy > -0.05:
			ball.vy = 0

#uses more friction to slow the ball
def slowCueBall(ball):
	if ball.vx > 0:
		ball.vx -= ball.friction * 3
		if ball.vx < 0.05:
			ball.vx = 0
	elif ball.vx < 0:
		ball.vx += ball.friction * 3
		if ball.vx > -0.05:
			ball.vx = 0
	if ball.vy > 0:
		ball.vy -= ball.friction * 3
		if ball.vy < 0.05:
			ball.vy = 0
	elif ball.vy < 0:
		ball.vy += ball.friction * 3
		if ball.vy > -0.05:
			ball.vy = 0

#detecting ball to ball collisions
def collision(x1,y1,x2,y2):
	dist = distance(x1,y1,x2,y2)
	if dist < cueBall.radius*2:
		return True
	return False

#colliding and keeping the balls within the table
def collideBalls():
	Ball.hitBorder(cueBall)
	for ball1 in allBalls:
		allBalls.remove(ball1)
		Ball.hitBorder(ball1)
		for ball2 in allBalls:
			c = collision(ball1.rect.centerx, ball1.rect.centery, ball2.rect.centerx, ball2.rect.centery)
			if c:
				ballCollide(ball1,ball2)
				Ball.collided(ball1,ball2)
				Ball.hitBorder(ball2)
		allBalls.add(ball1)
	for ball in allBalls:
		c = collision(ball.rect.centerx, ball.rect.centery, cueBall.rect.centerx, cueBall.rect.centery)
		if c:
			Ball.hitBorder(ball)
			ballCollide(ball,cueBall)
			Ball.collided(cueBall,ball)

#vertical alignment to display the balls the player needs to hit
vSpace = height//7
vGap = vSpace*0.2
playerBallLocations = [(vSpace+vGap),(vSpace*2+vGap),(vSpace*3+vGap),(vSpace*4+vGap),(vSpace*5+vGap),(vSpace*6+vGap),(vSpace*7+vGap)]
player = True #determines which player's turn it is

class Player(object):
	def __init__(self, name, ballType, num):
		self.name = name
		self.ballType = ballType
		self.num = num
		self.nameColor = (0,0,0)
		self.gameScreenGap = poolTable.length + poolTable.margin

	def drawPlayer(self):
		font = pygame.font.SysFont("Calibri", 30) 
		gap = (width - self.gameScreenGap)//2.8
		text = font.render(f"{self.name}", False,  self.nameColor)
		textRect = text.get_rect()
		textRect.centerx = self.gameScreenGap + gap*self.num
		textRect.centery = poolTable.margin
		ballGap = cueBall.radius*1.5
		screen.blit(text, textRect)

	def displayBalls(self):
		count = 0
		ballGap = width//30
		gap = (width - self.gameScreenGap)//2.8
		if self.ballType == "Stripe": 
			for b in stripeBalls:
				x = int(self.gameScreenGap + gap*self.num)
				y = int(poolTable.margin*2 + ballGap*count)
				pygame.draw.circle(screen, b.color, (x,y), b.radius)
				pygame.draw.line(screen, (255,255,255), (x,y-b.radius), \
							(x,y+b.radius), 3)
				count += 1
		elif self.ballType == "Solid": 
			for b in solidBalls:
				x = int(self.gameScreenGap + gap*self.num)
				y = int(poolTable.margin*2 + ballGap*count)
				pygame.draw.circle(screen, b.color, (x,y), b.radius)
				
				count += 1


player1 = Player("player1","Stripe",1)
player2 = Player("player2","Solid",2)

def determinePlayer():
	pass


#drawing the screen and every thing on it
def redrawAll():
	allBalls.update()
	poolTable.drawTable()
	cueStick.drawStick(cueBall.rect.centerx, cueBall.rect.centery)
	if cueBall.vx == 0 and cueBall.vy == 0:
		cueStick.drawPredictions(cueBall.rect.centerx, cueBall.rect.centery)
	for p in pockets:
		p.drawPockets()
	cueBall.drawBall(cueBall.rect.center)
	allBalls.draw(screen)
	for b in allBalls:
		b.drawBall(b.rect.center)
	player1.drawPlayer()
	player2.drawPlayer()
	cueStick.showForce()
	player1.displayBalls()
	player2.displayBalls()

#when scratches occur
draggingCueBall = False
helpscreen = False
openingScreen = startScreen()

openingScreen.run()
class PlayPool(object):
	gameOver = False
	while not gameOver:
		time.tick(60)
		for event in pygame.event.get(): #returns a list of all the events that have happened
			if event.type == pygame.QUIT:
				gameOver = True		
			if event.type == pygame.MOUSEBUTTONDOWN:
				forces = cueStick.shoot(cueStick.force,cueBall) 
			if event.type == pygame.MOUSEMOTION:
				if draggingCueBall:
					x, y = pygame.mouse.get_pos()
					cueBall.rect.centerx, cueBall.rect.centery = x, y
			if event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1:
					draggingCueBall = False
			if event.type == pygame.KEYDOWN:
				if pygame.key.get_pressed()[pygame.K_UP]:
					cueStick.force += 5 
				elif pygame.key.get_pressed()[pygame.K_DOWN]:
					cueStick.force -= 5
				elif pygame.key.get_pressed()[pygame.K_i]:
					cueStick.ballNum += 1
				elif pygame.key.get_pressed()[pygame.K_d]:
					cueStick.ballNum -= 1
				elif pygame.key.get_pressed()[pygame.K_SPACE]:
					helpscreen = not helpscreen
				cueStick.ballNum %= 16
				cueStick.force %= 55

		collideBalls()
		for b in allBalls:
			slowBall(b)
		slowBall(cueBall)

		if helpscreen:
			font = pygame.font.SysFont("Calibri", 30) 
			text = font.render("Press 'i' or 'd' to navigate between the balls('i' increases the ball num. and 'd' decreases\nUse 'up' and 'down'" +
								"arrow keys to increase and decrease force \nShoot by simply clicking your mousepad/mouse", False,  (0,0,0))
			textRect = text.get_rect()
			textRect.centerx = (poolTable.margin + poolTable.length)//2
			textRect.centery = (poolTable.margin + poolTable.width)//2
			screen.blit(text, textRect)

		#checking for balls that entered a pocket
		for p in pockets:
			for b in allBalls:
				result = ballInPocket(p, b)
				if result:
					if b in solidBalls:
						solidBalls.remove(b)
					elif b in stripeBalls:
						stripeBalls.remove(b)
					if b == eightBall and len(allBalls) != 0:
						gameOver = True
			if ballInPocket(p, cueBall):
				draggingCueBall = True 
				cueBall.rect.centerx = poolTable.length * (3/4) + poolTable.margin
				cueBall.rect.centery = poolTable.width*0.5 + poolTable.margin
				cueBall.vx = 0
				cueBall.vy = 0
				cueStick.force = 0
		pygame.display.flip()
		screen.fill((169,163,143))
		redrawAll()
		pygame.display.update()

pygame.quit()

