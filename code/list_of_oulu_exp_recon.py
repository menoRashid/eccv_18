from train_test_caps import *
from torchvision import datasets, transforms
import models

import os
from helpers import util,visualize,augmenters
import random
import dataset
import numpy as np


def trying_out_recon(wdecay,lr):
    for split_num in [4,9]:
        out_dir_meta = '../experiments/oulu_with_recon_0.5_r3/'
        route_iter = 3
        num_epochs = 100
        epoch_start = 0
        # dec_after = ['exp',0.96,3,1e-6]
        dec_after = ['step',100,0.1]


        lr = lr
        # [0.001]
        pool_type = 'max'
        im_size = 96
        model_name = 'khorrami_capsule_reconstruct'
        save_after = 50
        type_data = 'three_im_no_neutral_just_strong'; n_classes = 6;

        # strs_append = '_'.join([str(val) for val in ['all_aug','wdecay',wdecay,pool_type,500,'step',500,0.1]+lr])
        # out_dir_train = os.path.join(out_dir_meta,'oulu_'+type_data+'_'+str(split_num)+'_'+strs_append)
        # model_file = os.path.join(out_dir_train,'model_499.pt')
        # type_data = 'single_im'
        model_file = None
        

        criterion = 'margin'
        margin_params = None
        spread_loss_params = dict(end_epoch=int(num_epochs*0.5),decay_steps=5,init_margin = 0.5, max_margin = 0.5)
        # spread_loss_params = {'end_epoch':int(num_epochs*0.9),'decay_steps':5,'init_margin' : 0.9, 'max_margin' : 0.9}
        

        strs_append = '_'.join([str(val) for val in ['justflip','wdecay',wdecay,pool_type,num_epochs]+dec_after+lr])
        out_dir_train = os.path.join(out_dir_meta,'oulu_'+type_data+'_'+str(split_num)+'_'+strs_append)
        print out_dir_train

        train_file = os.path.join('../data/Oulu_CASIA','train_test_files_preprocess_maheen_vl_gray',type_data,'train_'+str(split_num)+'.txt')
        test_file = os.path.join('../data/Oulu_CASIA','train_test_files_preprocess_maheen_vl_gray',type_data,'test_'+str(split_num)+'.txt')
        mean_std_file = os.path.join('../data/Oulu_CASIA','train_test_files_preprocess_maheen_vl_gray',type_data,'train_'+str(split_num)+'_mean_std_val_0_1.npy')
        
        class_weights = util.get_class_weights(util.readLinesFromFile(train_file))

        mean_std = np.load(mean_std_file)

        print mean_std

        data_transforms = {}
        data_transforms['train']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_size,im_size)),
            # transforms.Resize((102,102)),
            # transforms.RandomCrop(im_size),
            transforms.RandomHorizontalFlip(),
            # transforms.RandomRotation(15),
            # transforms.ColorJitter(),
            transforms.ToTensor(),
            transforms.Normalize([float(mean_std[0])],[float(mean_std[1])])
        ])
        data_transforms['val']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_size,im_size)),
            transforms.ToTensor(),
            transforms.Normalize([float(mean_std[0])],[float(mean_std[1])])
            ])
        # data_transforms['val_center']= transforms.Compose([
        #     transforms.ToPILImage(),
        #     transforms.Resize((102,102)),
        #     transforms.CenterCrop(im_size),
        #     transforms.ToTensor(),
        #     transforms.Normalize([float(mean_std[0])],[float(mean_std[1])])
        #     ])

        train_data = dataset.Oulu_Static_Dataset(train_file, data_transforms['train'])
        test_data = dataset.Oulu_Static_Dataset(test_file,  data_transforms['val'])
        # test_data_center = dataset.Oulu_Static_Dataset(test_file,  data_transforms['val_center'])
        
        network_params = dict(n_classes=n_classes,spread_loss_params = spread_loss_params,pool_type=pool_type,r=route_iter,init=False,reconstruct=True,class_weights = class_weights)
        
        batch_size = 64
        batch_size_val = 64


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
                    criterion = criterion,
                    gpu_id = 0,
                    num_workers = 0,
                    model_file = model_file,
                    epoch_start = epoch_start,
                    margin_params = margin_params,
                    network_params = network_params,
                    weight_decay=wdecay)

        print train_params
        param_file = os.path.join(out_dir_train,'params.txt')
        all_lines = []
        for k in train_params.keys():
            str_print = '%s: %s' % (k,train_params[k])
            print str_print
            all_lines.append(str_print)
        util.writeFile(param_file,all_lines)

        train_model(**train_params)

        test_params = dict(out_dir_train = out_dir_train,
                model_num = num_epochs-1, 
                train_data = train_data,
                test_data = test_data,
                gpu_id = 0,
                model_name = model_name,
                batch_size_val = batch_size_val,
                criterion = criterion,
                margin_params = margin_params,
                network_params = network_params)
        test_model(**test_params)
        
        # test_params['test_data'] = test_data_center
        # test_params['post_pend'] = '_center'
        # test_model(**test_params)


def main():
    trying_out_recon(0,[0.001])


if __name__=='__main__':
    main()