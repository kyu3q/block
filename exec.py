# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *
import math
import sys
import pygame.mixer
import stage
import numpy as np
import random
import os

# 画面サイズ
SCREEN = Rect(0, 0, 560, 600)
# ファイルパス
FILE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"

# バドルのクラス
class Paddle(pygame.sprite.Sprite):
    # コンストラクタ（初期化メソッド）
    def __init__(self, filename, blocks, score, heart):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load(filename).convert()
        self.rect = self.image.get_rect()
        self.rect.bottom = SCREEN.bottom - 20          # パドルのy座標
        self.rect.centerx = SCREEN.centerx             # パドルのx座標
        self.score = score
        self.heart = heart
        self.blocks = blocks  # ブロックグループへの参照
        self.balls_count = 1
        self.add_ball_cnt = 0

    def update(self):
        # キーイベント処理(キャラクタ画像の移動)
        pressed_key = pygame.key.get_pressed()
        if pressed_key[K_LEFT]:
            self.rect.centerx -= 7
        # 「←」「→」キーが押されたらx座標を移動
        if pressed_key[K_RIGHT]:
            self.rect.centerx += 7
        self.rect.clamp_ip(SCREEN)  # ゲーム画面内のみで移動

    def add_ball(self, function):
        self.add_ball_cnt += function

    def kill_ball(self):
        self.balls_count -= 1

    def create_ball(self):
        if self.add_ball_cnt > 0:
            Ball(FILE_PATH + "picture/ball.png",
                 self, 7, 135, 45, 1)
            self.add_ball_cnt -= 1
            self.balls_count += 1


# ボールのクラス
class Ball(pygame.sprite.Sprite):
    # コンストラクタ（初期化メソッド）
    def __init__(self, filename, paddle, speed, angle_left, angle_right, add_flg):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load(filename).convert()
        self.image = pygame.transform.scale(self.image, (15, 15))
        self.rect = self.image.get_rect()
        self.dx = self.dy = 0  # ボールの速度
        self.paddle = paddle  # パドルへの参照
        self.hit = 0  # 連続でブロックを壊した回数
        self.speed = speed  # ボールの初期速度
        self.angle_left = angle_left  # パドルの反射方向(左端:135度）
        self.angle_right = angle_right  # パドルの反射方向(右端:45度）
        if add_flg == 1:
            # ボールの初期位置
            self.dx = self.speed * math.cos(0.5)
            self.dy = -self.speed * math.sin(0.5)
            self.rect.centerx = self.paddle.rect.centerx
            self.rect.bottom = self.paddle.rect.top
            self.update = self.move
        else:
            self.update = self.start  # ゲーム開始状態に更新

    # ゲーム開始状態（マウスを左クリック時するとボール射出）
    def start(self):
        # ボールの初期位置(パドルの上)
        self.rect.centerx = self.paddle.rect.centerx
        self.rect.bottom = self.paddle.rect.top

        # キーイベント処理(キャラクタ画像の移動)
        pressed_key = pygame.key.get_pressed()
        # キーボード左右移動でボール射出
        if pressed_key[K_LEFT]:
            self.dx = self.speed * math.cos(0.5)
            self.dy = -self.speed * math.sin(0.5)
            self.update = self.move
        if pressed_key[K_RIGHT]:
            self.dx = -self.speed * math.cos(0.5)
            self.dy = -self.speed * math.sin(0.5)
            self.update = self.move

    def delete(self):
        self.kill()

    # ボールの挙動
    def move(self):
        self.rect.centerx += self.dx
        self.rect.centery += self.dy

        # 壁との反射
        if self.rect.left < SCREEN.left:    # 左側
            self.rect.left = SCREEN.left
            self.dx = -self.dx              # 速度を反転
        if self.rect.right > SCREEN.right:  # 右側
            self.rect.right = SCREEN.right
            self.dx = -self.dx
        if self.rect.top < SCREEN.top:      # 上側
            self.rect.top = SCREEN.top
            self.dy = -self.dy

        # パドルとの反射(左端:135度方向, 右端:45度方向, それ以外:線形補間)
        # 2つのspriteが接触しているかどうかの判定
        if self.rect.colliderect(self.paddle.rect) and self.dy > 0:
            self.hit = 0                                # 連続ヒットを0に戻す
            (x1, y1) = (self.paddle.rect.left - self.rect.width, self.angle_left)
            (x2, y2) = (self.paddle.rect.right, self.angle_right)
            x = self.rect.left                          # ボールが当たった位置
            y = (float(y2-y1)/(x2-x1)) * (x - x1) + y1  # 線形補間
            angle = math.radians(y)                     # 反射角度
            self.dx = self.speed * math.cos(angle)
            self.dy = -self.speed * math.sin(angle)
            # self.paddle_sound.play()                    # 反射音

        # ボールを落とした場合
        if self.rect.top > SCREEN.bottom:

            if self.paddle.balls_count == 1 and self.paddle.heart.heart_cnt > 1:

                self.update = self.start                    # ボールを初期状態に
                self.hit = 0

                self.game_over_sound.play()
                self.paddle.score.add_score(-100)                  # スコア減点-100点
                self.paddle.heart.lost_heart()                     # ハート減点 -1

            elif self.paddle.balls_count == 1 and self.paddle.heart.heart_cnt == 1:

                self.game_over_sound.play()
                self.paddle.score.add_score(-100)                  # スコア減点-100点
                self.paddle.heart.lost_heart()                     # ハート減点 -1

                self.update = self.delete
                self.paddle.kill_ball()
            else:
                self.update = self.delete
                self.paddle.kill_ball()

        # ボールと衝突したブロックリストを取得（Groupが格納しているSprite中から、指定したSpriteと接触しているものを探索）
        blocks_collided = pygame.sprite.spritecollide(self, self.paddle.blocks, False)
        if blocks_collided:  # 衝突ブロックがある場合
            old_rect = self.rect
            for block in blocks_collided:
                # ボールが左からブロックへ衝突した場合
                if old_rect.left < block.rect.left and old_rect.right < block.rect.right:
                    self.rect.right = block.rect.left
                    self.dx = -self.dx
                    
                # ボールが右からブロックへ衝突した場合
                if block.rect.left < old_rect.left and block.rect.right < old_rect.right:
                    self.rect.left = block.rect.right
                    self.dx = -self.dx

                # ボールが上からブロックへ衝突した場合
                if old_rect.top < block.rect.top and old_rect.bottom < block.rect.bottom:
                    self.rect.bottom = block.rect.top
                    self.dy = -self.dy

                # ボールが下からブロックへ衝突した場合
                if block.rect.top < old_rect.top and block.rect.bottom < old_rect.bottom:
                    self.rect.top = block.rect.bottom
                    self.dy = -self.dy
                self.block_sound.play()     # 効果音を鳴らす
                self.hit += 1               # 衝突回数
                self.paddle.score.add_score(self.hit * 10)   # 衝突回数に応じてスコア加点
                block.cnt -= 1
                if block.cnt == 0:
                    block.kill()
                    if block.function > 0:
                        # ボールを作成
                        self.paddle.add_ball(block.function)
                        self.block_sound_2.play()


# ブロックのクラス
class Block(pygame.sprite.Sprite):
    def __init__(self, filename, x, y, cnt, function):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load(filename).convert()
        self.image = pygame.transform.scale(self.image, (40, 30))
        self.rect = self.image.get_rect()
        # ブロックの左上座標
        self.rect.left = SCREEN.left + x * self.rect.width
        self.rect.top = SCREEN.top + y * self.rect.height + 30
        # ブロックに打つ必要の回数
        self.cnt = cnt
        self.function = function  # 崩した時の変化
        self.sys_font = pygame.font.SysFont(None, 25)

    def draw(self, screen):
        # ブロックに打つ必要の回数を表示

        text = ""
        display_x = self.rect.centerx-5
        display_y = self.rect.centery-7

        if self.function > 0:
            text = "?"

        elif self.cnt > 1:
            text = str(self.cnt)
            if 10 <= self.cnt < 100:
                display_x = self.rect.centerx-10
            elif self.cnt >= 100:
                display_x = self.rect.centerx - 15

        if text != "":
            cnt_image = self.sys_font.render(text, True, (255, 255, 255))
            screen.blit(cnt_image, (display_x, display_y))


# スコアのクラス
class Score:
    def __init__(self, x, y):
        self.sys_font = pygame.font.SysFont(None, 20)
        self.score = 0
        (self.x, self.y) = (x, y)

    def draw(self, screen):
        img = self.sys_font.render("paddle.score:"+str(self.score), True, (255, 255, 250))
        screen.blit(img, (self.x, self.y))

    def add_score(self, x):
        self.score += x


# ハートのクラス
class Heart:
    def __init__(self):
        self.sys_font = pygame.font.SysFont(None, 30)
        self.sys_font_2 = pygame.font.SysFont(None, 100)
        self.heart_cnt = 3

    def draw(self, screen):
        heart_text = ""
        for index in range(self.heart_cnt):
            heart_text += "@ "

        if self.heart_cnt > 0:
            img = self.sys_font.render(heart_text, True, (255, 255, 250))
            screen.blit(img, (450, 10))
        else:
            img = self.sys_font_2.render("GAME OVER!", True, (255, 255, 250))
            screen.blit(img, (40, 250))

    def lost_heart(self):
        self.heart_cnt -= 1


def sub_main(stage_cnt):
    pygame.init()
    screen = pygame.display.set_mode(SCREEN.size)
    bg = pygame.image.load(FILE_PATH + "picture/background.jpg").convert_alpha()    # 背景画像の取得
    rect_bg = bg.get_rect()

    # Ball.paddle_sound = pygame.mixer.Sound(FILE_PATH + "music/flashing.wav")    # パドルにボールが衝突した時の効果音取得
    Ball.block_sound = pygame.mixer.Sound(FILE_PATH + "music/striking_a_small_stone.wav")    # ブロックにボールが衝突した時の効果音取得
    Ball.block_sound_2 = pygame.mixer.Sound(FILE_PATH + "music/po.wav")    # ブロックにボールが衝突した時の効果音取得

    Ball.game_over_sound = pygame.mixer.Sound(FILE_PATH + "music/blackout.wav")    # ゲームオーバー時の効果音取得
    Ball.game_clear_sound = pygame.mixer.Sound(FILE_PATH + "music/blackout_dulcimer2.wav")    # ゲームオーバー時の効果音取得

    # 描画用のスプライトグループ
    group = pygame.sprite.RenderUpdates()

    # 衝突判定用のスプライトグループ
    blocks = pygame.sprite.Group()
    balls = pygame.sprite.Group()

    # スプライトグループに追加
    Paddle.containers = group
    Ball.containers = group, balls
    Block.containers = group, blocks

    # スコアを画面に表示
    score = Score(10, 10)
    # ハートを画面に表示
    heart = Heart()

    # ブロックの作成
    for x in range(np.shape(stage.stage)[2]):
        for y in range(np.shape(stage.stage)[1]):
            if stage.stage[stage_cnt][y][x] > 0:
                Block(FILE_PATH + "picture/block_" + str(stage.stage[stage_cnt][y][x]) + ".png",
                      x, y, stage.stage[stage_cnt][y][x],
                      3*random.randrange(3+int(stage_cnt/10))*random.randrange(2))

    # パドルの作成
    paddle = Paddle(FILE_PATH + "picture/paddle.png", blocks, score, heart)

    # ボールを作成
    Ball(FILE_PATH + "picture/ball.png", paddle, 7, 135, 45, 0)

    clock = pygame.time.Clock()
    ball_create_flg = True

    while 1:

        clock.tick(60)  # フレームレート(60fps)
        screen.fill((0, 20, 0))
        screen.blit(bg, rect_bg)  # 背景画像の描画
        # 全てのスプライトグループを更新
        group.update()
        # 全てのスプライトグループを描画

        # ボールの追加
        if ball_create_flg:
            paddle.create_ball()
            ball_create_flg = False
        else:
            ball_create_flg = True
        group.draw(screen)
        # ブロックに打つ必要の回数を表示
        for block in blocks:
            block.draw(screen)
        # スコアを描画
        score.draw(screen)
        # ハートを描画"
        heart.draw(screen)
        for ball in balls:
            if ball.update == ball.start and heart.heart_cnt == 3:
                # ステージ表示
                screen.blit(pygame.font.SysFont(None, 70).render("Stage " + str(stage_cnt + 1), True,
                                                                 (222, 222, 222)), (170, 300))

        # GameOver
        if len(blocks) == 0:

            if stage_cnt == np.shape(stage.stage)[0] - 1:
                screen.blit(pygame.font.SysFont(None, 100).render("CLEAR~ (*^_^*)", True, (255, 255, 250)), (30, 250))
                for ball in balls:
                    ball.kill()
                    paddle.balls_count = 0
            else:
                Ball.game_clear_sound.play()
                break

        if paddle.balls_count > 0:
            screen.blit(pygame.font.SysFont(None, 30).render("Ball:" + str(paddle.balls_count),
                                                             True, (255, 255, 250)), (450, 550))

        # 画面更新./;:
        pygame.display.update()

        # キーイベント（終了）
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_SPACE:
                main()


def main():
    for i in range(np.shape(stage.stage)[0]):
        sub_main(i)


if __name__ == "__main__":
    main()


