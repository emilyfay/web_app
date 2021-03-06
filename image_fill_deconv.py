#!/usr/bin/env python2.7

import os
from scipy import ndimage
import numpy as np

from model import DCGAN

import tensorflow as tf

flags = tf.app.flags
flags.DEFINE_integer("epoch", 100, "Epoch to train [25]")
flags.DEFINE_float("learning_rate", 0.0005, "Learning rate of for adam [0.0002]")
flags.DEFINE_float("beta1", 0.5, "Momentum term of adam [0.5]")
flags.DEFINE_integer("train_size", np.inf, "The size of train images [np.inf]")
flags.DEFINE_integer("batch_size", 1, "The size of batch images [64]")
flags.DEFINE_integer("image_size", 64, "The size of image to use")
flags.DEFINE_string("dataset", "./data/masked", "Dataset directory.")
flags.DEFINE_string("image_path", "data/masked/test2.png", "Image path.")
flags.DEFINE_string("out_path", "data/filled/test2.png", "output path.")
flags.DEFINE_string("checkpoint_dir", "final_checkpoint_deconv", "Directory name to save the checkpoints [checkpoint]")
flags.DEFINE_string("sample_dir", "filled", "Directory name to save the image samples [samples]")
FLAGS = flags.FLAGS

masked_image = ndimage.imread(FLAGS.image_path, mode='RGB')
print('got image')

if not os.path.exists(FLAGS.checkpoint_dir):
    os.makedirs(FLAGS.checkpoint_dir)
if not os.path.exists(FLAGS.sample_dir):
    os.makedirs(FLAGS.sample_dir)

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
with tf.Session(config=config) as sess:
    dcgan = DCGAN(sess, image_size=64, batch_size=1,
                  is_crop=False, checkpoint_dir=FLAGS.checkpoint_dir, out_path = FLAGS.out_path)

    dcgan.infill(masked_image)

