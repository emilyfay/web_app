# Original Version: Taehoon Kim (http://carpedm20.github.io)
#   + Source: https://github.com/carpedm20/DCGAN-tensorflow/blob/e30539fb5e20d5a0fed40935853da97e9e55eee8/model.py
#   + License: MIT
# [2016-08-05] Modifications for Completion: Brandon Amos (http://bamos.github.io)
#   + License: MIT

from __future__ import division
import os
from glob import glob
import tensorflow as tf
import numpy as np
from six.moves import xrange

from Image_completer.ops import *
from Image_completer.utils import *

class DCGAN(object):
    def __init__(self, sess, image_size=64, is_crop=False,
                 batch_size=64, sample_size=64,
                 z_dim=100, gf_dim=64, df_dim=64,
                 gfc_dim=1024, dfc_dim=1024, c_dim=3,
                 checkpoint_dir=None, lam=0.1):
        """

        Args:
            sess: TensorFlow session
            batch_size: The size of batch. Should be specified before training.
            z_dim: (optional) Dimension of dim for Z. [100]
            gf_dim: (optional) Dimension of gen filters in first conv layer. [64]
            df_dim: (optional) Dimension of discrim filters in first conv layer. [64]
            gfc_dim: (optional) Dimension of gen untis for for fully connected layer. [1024]
            dfc_dim: (optional) Dimension of discrim units for fully connected layer. [1024]
            c_dim: (optional) Dimension of image color. [3]
        """
        self.sess = sess
        self.is_crop = is_crop
        self.batch_size = batch_size
        self.image_size = image_size
        self.sample_size = sample_size
        self.image_shape = [image_size, image_size, 3]

        self.gf_dim = gf_dim
        self.df_dim = df_dim

        self.gfc_dim = gfc_dim
        self.dfc_dim = dfc_dim

        self.lam = lam

        self.c_dim = 3

        # batch normalization : deals with poor initialization helps gradient flow
        self.d_bn1 = batch_norm(name='d_bn1')
        self.d_bn2 = batch_norm(name='d_bn2')
        self.d_bn3 = batch_norm(name='d_bn3')

        self.g_bn0 = batch_norm(name='g_bn0')
        self.g_bn1 = batch_norm(name='g_bn1')
        self.g_bn2 = batch_norm(name='g_bn2')
        self.g_bn3 = batch_norm(name='g_bn3')
        self.g_bn4 = batch_norm(name='g_bn4')
        self.g_bn5 = batch_norm(name='g_bn5')

        self.checkpoint_dir = checkpoint_dir
        self.build_model()
        self.model_name = "DCGAN.model"


    def build_model(self):
        self.images = tf.placeholder(
            tf.float32, [None] + self.image_shape, name='real_images')
        self.sample_images= tf.placeholder(
            tf.float32, [None] + self.image_shape, name='sample_images')
        #updated
        self.z= tf.placeholder(
            tf.float32, [None] + self.image_shape, name='mask_images')

        #updated
        self.G = self.generator(self.z)
        self.D, self.D_logits = self.discriminator(self.images)

        self.sampler = self.sampler(self.z)
        self.D_, self.D_logits_ = self.discriminator(self.G, reuse=True)

        self.d_sum = tf.histogram_summary("d", self.D)
        self.d__sum = tf.histogram_summary("d_", self.D_)
        self.G_sum = tf.image_summary("G", self.G)

        self.d_loss_real = tf.reduce_mean(
            tf.nn.sigmoid_cross_entropy_with_logits(self.D_logits,
                                                    tf.ones_like(self.D)))
        self.d_loss_fake = tf.reduce_mean(
            tf.nn.sigmoid_cross_entropy_with_logits(self.D_logits_,
                                                    tf.zeros_like(self.D_)))
        self.g_loss = tf.reduce_mean(
            tf.nn.sigmoid_cross_entropy_with_logits(self.D_logits_,
                                                    tf.ones_like(self.D_)))

        self.d_loss_real_sum = tf.scalar_summary("d_loss_real", self.d_loss_real)
        self.d_loss_fake_sum = tf.scalar_summary("d_loss_fake", self.d_loss_fake)

        self.d_loss = self.d_loss_real + self.d_loss_fake

        self.g_loss_sum = tf.scalar_summary("g_loss", self.g_loss)
        self.d_loss_sum = tf.scalar_summary("d_loss", self.d_loss)

        t_vars = tf.trainable_variables()

        self.d_vars = [var for var in t_vars if 'd_' in var.name]
        self.g_vars = [var for var in t_vars if 'g_' in var.name]

        self.saver = tf.train.Saver(max_to_keep=1)

        # Completion.
        self.mask = tf.placeholder(tf.float32, [None] + self.image_shape, name='mask')
        self.sess.run(tf.initialize_all_variables())
        print('Initialized')


    def discriminator(self, image, reuse=False):
        if reuse:
            tf.get_variable_scope().reuse_variables()
        h0 = lrelu(conv2d(image, self.df_dim, name='d_h0_conv'))
        h1 = lrelu(conv2d(h0, self.df_dim*2, name='d_h1_conv'))
        h2 = lrelu(conv2d(h1, self.df_dim*4, name='d_h2_conv'))
        h3 = lrelu(conv2d(h2, self.df_dim*8, name='d_h3_conv'))
        h4 = linear(tf.reshape(h3, [-1, 8192]), 1, 'd_h3_lin')

        return tf.nn.sigmoid(h4), h4

    def generator(self, z_image):

        h0 = lrelu(conv2d(z_image, self.gf_dim, d_h=1, d_w=1,name='g_h0'))
        h1 = lrelu(self.g_bn1(conv2d(h0, self.gf_dim, d_h=1, d_w=1,name='g_h1')))
        #h2 = lrelu(self.g_bn2(conv2d(h1, self.gf_dim, d_h=1, d_w=1,name='g_h2')))
        h2 = lrelu(self.g_bn2(conv2d(h1, self.gf_dim*2, name='g_h2')))
        #h3 = lrelu(self.g_bn3(conv2d(h2, self.gf_dim, d_h=1, d_w=1,name='g_h3')))
        h3, self.h3_w, self.h3_b = conv2d_transpose(h2,
            [self.batch_size, 64, 64, self.gf_dim], name='g_h3', with_w=True)
        h3 = tf.nn.relu(self.g_bn3(h3))
        h4 = lrelu(self.g_bn4(conv2d(h3, self.gf_dim, d_h=1, d_w=1, name='g_h4')))
        h5 = lrelu(self.g_bn5(conv2d(h4, 3, k_h=3, k_w=3, d_h=1, d_w=1, name='g_h5')))

        return tf.nn.tanh(h5)


    def sampler(self, z_image):
        tf.get_variable_scope().reuse_variables()
        h0 = lrelu(conv2d(z_image, self.gf_dim, d_h=1, d_w=1,name='g_h0'))
        h1 = lrelu(self.g_bn1(conv2d(h0, self.gf_dim, d_h=1, d_w=1,name='g_h1')))
        h2 = lrelu(self.g_bn2(conv2d(h1, self.gf_dim*2, name='g_h2')))
        h3, self.h3_w, self.h3_b = conv2d_transpose(h2,
            [self.batch_size, 64, 64, self.gf_dim], name='g_h3', with_w=True)
        h3 = tf.nn.relu(self.g_bn3(h3))
        h4 = lrelu(self.g_bn4(conv2d(h3, self.gf_dim, d_h=1, d_w=1, name='g_h4')))
        h5 = lrelu(self.g_bn5(conv2d(h4, 3, k_h=3, k_w=3, d_h=1, d_w=1, name='g_h5')))

        return tf.nn.tanh(h5)


    def infill(self, masked_image):
        try:
            self.load(self.checkpoint_dir)
            print(" [*] Trained Load SUCCESS from %s" %self.checkpoint_dir)
        except:
            print(" [!] Load failed from %s" %self.checkpoint_dir)

        masked_image_mat = np.ndarray((1,64,64,3))
        masked_image_mat[0,:,:,:] = np.asarray(masked_image)
        filled_image = self.sess.run([self.sampler],{self.z: masked_image_mat})

        return filled_image[0][0,:,:,:]

    def load(self, checkpoint_dir):
        print(" [*] Reading checkpoints...")

        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
        if ckpt and ckpt.model_checkpoint_path:
            self.saver.restore(self.sess, ckpt.model_checkpoint_path)
            return True
        else:
            return False