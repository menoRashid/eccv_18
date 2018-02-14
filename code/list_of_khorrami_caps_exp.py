from train_test_caps import *
from torchvision import datasets, transforms
import models

import os
from helpers import util,visualize,augmenters
import random
import dataset
import numpy as np


def khorrami_exp():
    for split_num in range(0,1):
        out_dir_meta = '../experiments/khorrami_caps/'
        num_epochs = 200
        epoch_start = 0
        dec_after = ['exp',0.96,100,1e-6]
        # dec_after = ['step',50,0.5]
        lr = [0.001]
        pool_type = 'max'
        im_size = 96
        model_name = 'khorrami_capsule'
        save_after = 50
        model_file=None    

        strs_append = '_'.join([str(val) for val in [pool_type,num_epochs]+dec_after+lr])
        out_dir_train = os.path.join(out_dir_meta,'ck_'+str(split_num)+'_'+strs_append)
        print out_dir_train


        train_file = '../data/ck_96/train_test_files/train_'+str(split_num)+'.txt'
        test_file = '../data/ck_96/train_test_files/test_'+str(split_num)+'.txt'
        mean_file = '../data/ck_96/train_test_files/train_'+str(split_num)+'_mean.png'
        std_file = '../data/ck_96/train_test_files/train_'+str(split_num)+'_std.png'
        
        mean_im = scipy.misc.imread(mean_file).astype(np.float32)
        std_im = scipy.misc.imread(std_file).astype(np.float32)
        std_im[std_im==0]=1.
        list_of_to_dos = ['flip','rotate','scale_translate']
        # 'pixel_augment','flip','rotate','scale_translate']

        data_transforms = {}
        data_transforms['train']= transforms.Compose([
            lambda x: augmenters.augment_image(x,list_of_to_dos,mean_im,std_im,im_size),
            transforms.ToTensor(),
            lambda x: x*255.
        ])
        data_transforms['val']= transforms.Compose([
            transforms.ToTensor(),
            lambda x: x*255.
            ])

        train_data = dataset.CK_96_Dataset(train_file, mean_file, std_file, data_transforms['train'])
        test_data = dataset.CK_96_Dataset(test_file, mean_file, std_file, data_transforms['val'])
        
        network_params = dict(n_classes=8,pool_type=pool_type,r=3,init=True)
        
        batch_size = 128
        batch_size_val = 128


        util.makedirs(out_dir_train)
        
        train_params = dict(out_dir_train = out_dir_train,
                    train_data = train_data,
                    test_data = test_data,
                    batch_size = batch_size,
                    batch_size_val = batch_size_val,
                    num_epochs = num_epochs,
                    save_after = save_after,
                    disp_after = 1,
                    plot_after = 10,
                    test_after = 1,
                    lr = lr,
                    dec_after = dec_after, 
                    model_name = model_name,
                    criterion = 'margin',
                    gpu_id = 2,
                    num_workers = 0,
                    model_file = model_file,
                    epoch_start = epoch_start,
                    network_params = network_params)

        print train_params
        param_file = os.path.join(out_dir_train,'params.txt')
        all_lines = []
        for k in train_params.keys():
            str_print = '%s: %s' % (k,train_params[k])
            print str_print
            all_lines.append(str_print)
        util.writeFile(param_file,all_lines)

        train_model(**train_params)



def main():
    khorrami_exp()

if __name__=='__main__':
    main()