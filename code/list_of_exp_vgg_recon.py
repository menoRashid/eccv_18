from train_test_caps import *
from torchvision import datasets, transforms
import models

import os
from helpers import util,visualize,augmenters
import random
import dataset
import numpy as np
import torch
from analysis import getting_accuracy

def simple_train_preprocessed(wdecay,lr,route_iter,folds=[4,9],model_name='vgg_capsule_disfa',epoch_stuff=[30,60],res=False):
    out_dirs = []

    out_dir_meta = '../experiments/oulu_vgg_recon_r'+str(route_iter)+'_noinit_preprocessed_withaug'
    num_epochs = epoch_stuff[1]
    epoch_start = 0
    dec_after = ['step',epoch_stuff[0],0.1]

    # data/Oulu_CASIA/train_test_files_preprocess_vl/
    lr = lr
    im_resize = 256
    im_size = 224
    # model_name = 'vgg_capsule_disfa'
    save_after = 20
    type_data = 'three_im_no_neutral_just_strong_False'; n_classes = 6;


    strs_append = '_'+'_'.join([str(val) for val in [model_name,'all_aug','wdecay',wdecay,num_epochs]+dec_after+lr])
    pre_pend = 'oulu_'+type_data+'_'
    
    
    for split_num in folds:
        
        if res:
            strs_append = '_'.join([str(val) for val in [model_name,'all_aug','wdecay',wdecay,50,'step',50,0.1]+lr])
            out_dir_train = os.path.join(out_dir_meta,'oulu_'+type_data+'_'+str(split_num)+'_'+strs_append)
            model_file = os.path.join(out_dir_train,'model_49.pt')
            epoch_start = 50
        else:
            model_file = None    

        # model_file = '../experiments/oulu_vgg_r3_noinit/oulu_three_im_no_neutral_just_strong_False_4_vgg_capsule_disfa_bigprimary_all_aug_wdecay_0_100_step_100_0.1_0.0001_0.001/model_30.pt'
        # epoch_start = 30


        # type_data = 'single_im'
        
        

        criterion = 'margin'
        # torch.nn.CrossEntropyLoss()
        margin_params = None
        

        # strs_append = '_'.join([str(val) for val in [model_name,'all_aug','wdecay',wdecay,num_epochs]+dec_after+lr])
        # out_dir_train = os.path.join(out_dir_meta,'oulu_'+type_data+'_'+str(split_num)+'_'+strs_append)
        # print out_dir_train
        out_dir_train = os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
        final_model_file = os.path.join(out_dir_train,'model_'+str(num_epochs-1)+'.pt')
        if os.path.exists(final_model_file):
            print 'skipping',final_model_file
            continue 
        # lr[1]=lr[1]*dec_after[2]


        train_file = os.path.join('../data/Oulu_CASIA','train_test_files_preprocess_vl',type_data,'train_'+str(split_num)+'.txt')
        test_file = os.path.join('../data/Oulu_CASIA','train_test_files_preprocess_vl',type_data,'test_'+str(split_num)+'.txt')
        
        # mean_std = np.array([[129.1863,104.7624,93.5940],[1.,1.,1.]]) #rgb
        mean_std = np.array([[128.,128.,128.],[1.,1.,1.]]) #bgr
        print mean_std

        data_transforms = {}
        data_transforms['train']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_resize,im_resize)),
            transforms.RandomCrop(im_size),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            
            transforms.ToTensor(),
            lambda x: x*255,
            transforms.Normalize(mean_std[0,:],mean_std[1,:]),

        ])
        data_transforms['val']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_size,im_size)),
            transforms.ToTensor(),
            lambda x: x*255,
            transforms.Normalize(mean_std[0,:],mean_std[1,:]),
            # lambda x: x[[2, 1, 0],:, : ]
            ])

        train_data = dataset.Oulu_Static_Dataset(train_file, data_transforms['train'],color=True)
        test_data = dataset.Oulu_Static_Dataset(test_file,  data_transforms['val'],color=True)
        
        network_params = dict(n_classes=n_classes,loss=nn.CrossEntropyLoss(),in_size=im_size,r=route_iter,init=False)
        if lr[0]==0:
            batch_size = 128
            batch_size_val = 128
        else:
            batch_size = 32
            batch_size_val = 16

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
        
    getting_accuracy.print_accuracy(out_dir_meta,pre_pend,strs_append,folds,log='log.txt')


def simple_train_preprocessed_ck(wdecay,lr,route_iter,folds=[4,9],model_name='vgg_capsule_disfa',epoch_stuff=[30,60],res=False):
    out_dirs = []

    out_dir_meta = '../experiments/ck_vgg_recon_r'+str(route_iter)+'_noinit'
    num_epochs = epoch_stuff[1]
    epoch_start = 0
    dec_after = ['step',epoch_stuff[0],0.1]

    lr = lr
    im_resize = 256
    im_size = 224
    # model_name = 'vgg_capsule_disfa'
    save_after = 10
    type_data = 'train_test_files'; n_classes = 8;


    strs_append = '_'+'_'.join([str(val) for val in [model_name,'all_augc','wdecay',wdecay,num_epochs]+dec_after+lr])
    pre_pend = 'ck_'
    
    
    for split_num in folds:
        
        if res:
            strs_append = '_'.join([str(val) for val in [model_name,'all_augc','wdecay',wdecay,50,'step',50,0.1]+lr])
            out_dir_train = os.path.join(out_dir_meta,'ck_'+type_data+'_'+str(split_num)+'_'+strs_append)
            model_file = os.path.join(out_dir_train,'model_49.pt')
            epoch_start = 50
        else:
            model_file = None    

        # model_file = '../experiments/oulu_vgg_r3_noinit/oulu_three_im_no_neutral_just_strong_False_4_vgg_capsule_disfa_bigprimary_all_aug_wdecay_0_100_step_100_0.1_0.0001_0.001/model_30.pt'
        # epoch_start = 30


        # type_data = 'single_im'
        
        

        criterion = 'margin'
        # torch.nn.CrossEntropyLoss()
        margin_params = None
        

        # strs_append = '_'.join([str(val) for val in [model_name,'all_aug','wdecay',wdecay,num_epochs]+dec_after+lr])
        # out_dir_train = os.path.join(out_dir_meta,'oulu_'+type_data+'_'+str(split_num)+'_'+strs_append)
        # print out_dir_train
        out_dir_train = os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
        final_model_file = os.path.join(out_dir_train,'model_'+str(num_epochs-1)+'.pt')
        if os.path.exists(final_model_file):
            print 'skipping',final_model_file
            continue 
        # lr[1]=lr[1]*dec_after[2]


        train_file = os.path.join('../data/ck_256',type_data,'train_'+str(split_num)+'.txt')
        test_file = os.path.join('../data/ck_256',type_data,'test_'+str(split_num)+'.txt')
        
        # mean_std = np.array([[129.1863,104.7624,93.5940],[1.,1.,1.]]) #rgb
        mean_std = np.array([[128.,128.,128.],[1.,1.,1.]]) #bgr
        print mean_std

        data_transforms = {}
        data_transforms['train']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_resize,im_resize)),
            transforms.RandomCrop(im_size),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ToTensor(),
            lambda x: x*255,
            transforms.Normalize(mean_std[0,:],mean_std[1,:]),

        ])
        data_transforms['val']= transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((im_size,im_size)),
            transforms.ToTensor(),
            lambda x: x*255,
            transforms.Normalize(mean_std[0,:],mean_std[1,:]),
            # lambda x: x[[2, 1, 0],:, : ]
            ])

        train_data = dataset.Oulu_Static_Dataset(train_file, data_transforms['train'],color=True)
        test_data = dataset.Oulu_Static_Dataset(test_file,  data_transforms['val'],color=True)
        
        network_params = dict(n_classes=n_classes,loss=nn.CrossEntropyLoss(),in_size=im_size,r=route_iter,init=False)
        if lr[0]==0:
            batch_size = 128
            batch_size_val = 128
        else:
            batch_size = 32
            batch_size_val = 16

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
        
    getting_accuracy.print_accuracy(out_dir_meta,pre_pend,strs_append,folds,log='log.txt')


def main():
    
    folds = range(10)
    epoch_stuff = [50,50]
    lr = [0.00001,0.001,0.001]
    res=True
    route_iter = 3
    simple_train_preprocessed(0.000005, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_2class_withrecon', epoch_stuff=epoch_stuff,res=False)

    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigclass_withrecon', epoch_stuff=epoch_stuff,res=False)

    # simple_train_preprocessed_ck(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_withrecon', epoch_stuff=epoch_stuff,res=False)


    # return

    #more class
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigclass_withrecon', epoch_stuff=epoch_stuff,res=False)

    # #more primary same #param
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigprimary_lessdim_withrecon', epoch_stuff=epoch_stuff,res=False)
    # #more primary 
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigprimary_withrecon', epoch_stuff=epoch_stuff,res=False)
    # #more primary  and more class
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigprimary_bigclass_withrecon', epoch_stuff=epoch_stuff,res=False)

    #original with only some ft
    # lr = [0,0.0001,0.001,0.001]
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_lastft_withrecon', epoch_stuff=epoch_stuff,res=False)
    

    # #same class lower vgg lr
    # lr = [0.00001,0.001,0.001]
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_withrecon', epoch_stuff=epoch_stuff,res=False)

    # #more class lower vgg lr
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_bigclass_withrecon', epoch_stuff=epoch_stuff,res=False)


    # route_iter = 1
    # simple_train_preprocessed(0, lr=lr, route_iter = route_iter, folds= folds, model_name='vgg_capsule_disfa_withrecon', epoch_stuff=epoch_stuff,res=False)
    
    


if __name__=='__main__':
    main()