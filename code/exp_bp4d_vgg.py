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
# from helpers import util,visualize,augmenters
import save_visualizations


def train_vgg(wdecay,lr,route_iter,folds=[4,9],model_name='vgg_capsule_bp4d',epoch_stuff=[30,60],res=False, class_weights = False, reconstruct = False, loss_weights = None, exp = False, align = False, disfa = False,more_aug=False, dropout = None, model_to_test = None, gpu_id = 0, test_mode = False):
    out_dirs = []

    

    out_dir_meta = '../experiments/'+model_name+str(route_iter)
    num_epochs = epoch_stuff[1]

    if model_to_test is None:
        model_to_test = num_epochs-1

    epoch_start = 0
    if exp:
        dec_after = ['exp',0.96,epoch_stuff[0],1e-6]
    else:
        dec_after = ['step',epoch_stuff[0],0.1]

    lr = lr

    if model_name.startswith('vgg'):
        im_resize = 256
        im_size = 224
        if not disfa:
            dir_files = '../data/bp4d'
            if align:
                type_data = 'train_test_files_256_color_align'; n_classes = 12;
            else:
                type_data = 'train_test_files_256_color_nodetect'; n_classes = 12;
            pre_pend = 'bp4d_256_'+type_data+'_'
            binarize = False
        else:
            dir_files = '../data/disfa'
            type_data = 'train_test_8_au_all_method_256_color_align'; n_classes = 8;
            pre_pend = 'disfa_'+type_data+'_'
            binarize = True
            pre_pend = 'disfa_256_'+type_data+'_'
    else:
        if not disfa:
            im_resize = 110
            im_size = 96
            binarize = False
            dir_files = '../data/bp4d'
            type_data = 'train_test_files_110_color_align'; n_classes = 12;
            pre_pend = 'bp4d_110_'
        else:
            im_resize = 110
            im_size = 96
            dir_files = '../data/disfa'
            type_data = 'train_test_8_au_all_method_110_color_align'; n_classes = 8;
            binarize = True
            pre_pend = 'disfa_110_'+type_data+'_'

    save_after = 1
    criterion = 'marginmulti'
    criterion_str = criterion

    init = False

    strs_append_list = ['reconstruct',reconstruct,class_weights,'all_aug',criterion_str,init,'wdecay',wdecay,num_epochs]+dec_after+lr+[more_aug]+[dropout]
    if loss_weights is not None:
        strs_append_list = strs_append_list     +['lossweights']+loss_weights
    strs_append = '_'+'_'.join([str(val) for val in strs_append_list])
    
    
    
    lr_p=lr[:]
    for split_num in folds:
        
        if res:

            strs_append_list_c = ['reconstruct',reconstruct,False,'all_aug',criterion_str,init,'wdecay',wdecay,10]+['step',10,0.1]+lr+[more_aug]+[dropout]
            # print dec_after
            # raw_input()
            if loss_weights is not None:
                strs_append_list_c = strs_append_list_c+['lossweights']+loss_weights
            
            strs_append_c = '_'+'_'.join([str(val) for val in strs_append_list_c])
            out_dir_train = os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append_c)
            
            model_file = os.path.join(out_dir_train,'model_4.pt')
            epoch_start = 5
            lr = [val *0.1 for val in lr]
            print 'FILE EXISTS', os.path.exists(model_file), model_file, epoch_start
            
            raw_input()
            
        else:
            model_file = None    


        margin_params = None
        
        out_dir_train =  os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
        final_model_file = os.path.join(out_dir_train,'model_'+str(num_epochs-1)+'.pt')
        # final_model_file = os.path.join(out_dir_train,'results_model_'+str(model_to_test))
        if os.path.exists(final_model_file) and not test_mode:
            print 'skipping',final_model_file
            # raw_input()
            continue 
        else:
            print 'not skipping', final_model_file
            # raw_input()
            # continue

        train_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'.txt')
        test_file = os.path.join(dir_files,type_data,'test_'+str(split_num)+'.txt')

        data_transforms = None
        if model_name.startswith('vgg_capsule_7_3_imagenet') or model_name.startswith('scratch_'):
            # mean_std = np.array([[93.5940,104.7624,129.1863],[1.,1.,1.]]) #bgr
            # std_div = np.array([0.225*255,0.224*255,0.229*255])
            # print std_div
            # raw_input()
            mean_std=np.array([[0.485, 0.456, 0.406],
                        [0.229, 0.224, 0.225]])

            bgr= False
            normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            std_div = None

            data_transforms = {}
            data_transforms['train'] = [ transforms.ToPILImage(),
                transforms.RandomCrop(im_size),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(15),
                transforms.ColorJitter(),
                transforms.ToTensor(),
                normalize]
            data_transforms['val'] = [transforms.ToPILImage(),
                transforms.Resize((im_size,im_size)),
                transforms.ToTensor(),
                normalize]
            
            if torch.version.cuda.startswith('9'):
                data_transforms['train'].append(lambda x: x.float())
                data_transforms['val'].append(lambda x: x.float())

            data_transforms['train']= transforms.Compose(data_transforms['train'])
            data_transforms['val']= transforms.Compose(data_transforms['val'])

            train_data = dataset.Bp4d_Dataset(train_file, bgr = bgr, binarize = binarize, transform = data_transforms['train'])
            test_data = dataset.Bp4d_Dataset(test_file, bgr = bgr, binarize= binarize, transform = data_transforms['val'])


        elif model_name.startswith('vgg'):
            mean_std = np.array([[93.5940,104.7624,129.1863],[1.,1.,1.]]) #bgr
            std_div = np.array([0.225*255,0.224*255,0.229*255])
            print std_div
            # raw_input()
            bgr= True
        else:
            mean_std = np.array([[0.485*255, 0.456*255, 0.406*255],
                                     [0.229*255, 0.224*255, 0.225*255]])
            bgr= False
        
        print mean_std

        
        class_weights = util.get_class_weights_au(util.readLinesFromFile(train_file))
        
        if data_transforms is None:
            data_transforms = {}
            if more_aug=='MORE':
                print more_aug
                list_of_to_dos = ['flip','rotate','scale_translate']            
                
                # print torch.version.cuda
                # raw_input()
                if torch.version.cuda.startswith('9'):
                    # print 'HEYLO'
                    # raw_input()
                    data_transforms['train']= transforms.Compose([
                        lambda x: augmenters.random_crop(x,im_size),
                        lambda x: augmenters.augment_image(x,list_of_to_dos,color=True,im_size = im_size),
                        transforms.ToTensor(),
                        lambda x: x.float()
                    ])
                    data_transforms['val']= transforms.Compose([
                        transforms.ToTensor(),
                        lambda x: x.float()
                    ])
                else:
                    data_transforms['train']= transforms.Compose([
                        lambda x: augmenters.random_crop(x,im_size),
                        lambda x: augmenters.augment_image(x,list_of_to_dos,color=True,im_size = im_size),
                        transforms.ToTensor(),
                        lambda x: x*255,
                    ])
                    data_transforms['val']= transforms.Compose([
                        transforms.ToTensor(),
                        lambda x: x*255,
                    ])






                train_data = dataset.Bp4d_Dataset_with_mean_std_val(train_file, bgr = bgr, binarize = binarize, mean_std = mean_std, transform = data_transforms['train'])
                test_data = dataset.Bp4d_Dataset_with_mean_std_val(test_file, bgr = bgr, binarize= binarize, mean_std = mean_std, transform = data_transforms['val'], resize = im_size)
            elif more_aug=='LESS':
                # std_div = None
                data_transforms['train']= transforms.Compose([
                    transforms.ToPILImage(),
                    # transforms.Resize((im_resize,im_resize)),
                    transforms.RandomCrop(im_size),
                    transforms.RandomHorizontalFlip(),
                    transforms.RandomRotation(15),
                    transforms.ColorJitter(),
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
                    ])

                train_data = dataset.Bp4d_Dataset(train_file, bgr = bgr, binarize = binarize, transform = data_transforms['train'])
                test_data = dataset.Bp4d_Dataset(test_file, bgr = bgr, binarize= binarize, transform = data_transforms['val'])
            elif more_aug=='NONE':
                print 'NO AUGING'
                data_transforms['train']= transforms.Compose([
                    transforms.ToTensor(),
                    lambda x: x*255
                ])
                data_transforms['val']= transforms.Compose([
                    transforms.ToTensor(),
                    lambda x: x*255
                    ])
                train_data = dataset.Bp4d_Dataset_with_mean_std_val(train_file, bgr = bgr, binarize = binarize, mean_std = mean_std, transform = data_transforms['train'], resize = im_size)
                test_data = dataset.Bp4d_Dataset_with_mean_std_val(test_file, bgr = bgr, binarize= binarize, mean_std = mean_std, transform = data_transforms['val'], resize = im_size)
            else:
                raise ValueError('more_aug not valid')



        if dropout is not None:
            print 'RECONS',reconstruct
            network_params = dict(n_classes=n_classes,pool_type='max',r=route_iter,init=init,class_weights = class_weights, reconstruct = reconstruct,loss_weights = loss_weights,std_div = std_div, dropout = dropout)
        else:
            network_params = dict(n_classes=n_classes,pool_type='max',r=route_iter,init=init,class_weights = class_weights, reconstruct = reconstruct,loss_weights = loss_weights,std_div = std_div)
            
        batch_size = 32
        batch_size_val = 32
        
        util.makedirs(out_dir_train)
        
        train_params = dict(out_dir_train = out_dir_train,
                    train_data = train_data,
                    test_data = test_data,
                    batch_size = batch_size,
                    batch_size_val = batch_size_val,
                    num_epochs = num_epochs,
                    save_after = save_after,
                    disp_after = 1,
                    plot_after = 100,
                    test_after = 1,
                    lr = lr,
                    dec_after = dec_after, 
                    model_name = model_name,
                    criterion = criterion,
                    gpu_id = gpu_id,
                    num_workers = 0,
                    model_file = model_file,
                    epoch_start = epoch_start,
                    margin_params = margin_params,
                    network_params = network_params,
                    weight_decay=wdecay)
        test_params = dict(out_dir_train = out_dir_train,
                    model_num = model_to_test, 
                    train_data = train_data,
                    test_data = test_data,
                    gpu_id = gpu_id,
                    model_name = model_name,
                    batch_size_val = batch_size_val,
                    criterion = criterion,
                    margin_params = margin_params,
                    network_params = network_params,barebones=True)
        # test_params_train = dict(**test_params)
        # test_params_train['test_data'] = train_data_no_t
        # test_params_train['post_pend'] = '_train'

        print train_params
        param_file = os.path.join(out_dir_train,'params.txt')
        all_lines = []
        for k in train_params.keys():
            str_print = '%s: %s' % (k,train_params[k])
            print str_print
            all_lines.append(str_print)
        # util.writeFile(param_file,all_lines)

        # if reconstruct:
        if not test_mode:
            train_model_recon(**train_params)

        test_model_recon(**test_params)

        # test_params = dict(out_dir_train = out_dir_train,
        #             model_num = 4, 
        #             train_data = train_data,
        #             test_data = test_data,
        #             gpu_id = gpu_id,
        #             model_name = model_name,
        #             batch_size_val = batch_size_val,
        #             criterion = criterion,
        #             margin_params = margin_params,
        #             network_params = network_params,barebones=True)
        
        # test_model_recon(**test_params)
        
        
    getting_accuracy.print_accuracy(out_dir_meta,pre_pend,strs_append,folds,log='log.txt')


def save_test_results(wdecay,lr,route_iter,folds=[4,9],model_name='vgg_capsule_bp4d',epoch_stuff=[30,60],res=False, class_weights = False, reconstruct = False, loss_weights = None, models_to_test = None, exp = False, disfa = False):
    out_dirs = []

    out_dir_meta = '../experiments/'+model_name+str(route_iter)
    num_epochs = epoch_stuff[1]
    epoch_start = 0
    # dec_after = ['exp',0.96,epoch_stuff[0],1e-6]
    if exp:
        dec_after = ['exp',0.96,epoch_stuff[0],1e-6]
    else:
        dec_after = ['step',epoch_stuff[0],0.1]

    lr = lr
    im_resize = 110
    # 256
    im_size = 96
    # save_after = 1
    

    if disfa:
        dir_files = '../data/disfa'
        # type_data = 'train_test_10_6_method_110_gray_align'; n_classes = 10;
        type_data = 'train_test_8_au_all_method_110_gray_align'; n_classes = 8;
        pre_pend = 'disfa_'+type_data+'_'
        binarize = True
    else:
        dir_files = '../data/bp4d'
        type_data = 'train_test_files_110_gray_align'; n_classes = 12;
        pre_pend = 'bp4d_'+type_data+'_'
        binarize = False

    criterion = 'marginmulti'
    criterion_str = criterion

    init = False

    strs_append = '_'+'_'.join([str(val) for val in ['reconstruct',reconstruct,class_weights,'flipCrop',criterion_str,init,'wdecay',wdecay,num_epochs]+dec_after+lr+['lossweights']+loss_weights])
    
    # pre_pend = 'bp4d_110_'
    
    lr_p=lr[:]
    for split_num in folds:
        for model_num_curr in models_to_test:
            margin_params = None
            out_dir_train =  os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
            final_model_file = os.path.join(out_dir_train,'model_'+str(num_epochs-1)+'.pt')

            if os.path.exists(os.path.join(out_dir_train,'results_model_'+str(model_num_curr))):
                print 'exists',model_num_curr,split_num
                print out_dir_train
                # continue
            else:

                print 'does not exist',model_num_curr,split_num
                # print 'bp4d_train_test_files_110_gray_align_0_reconstruct_True_True_flipCrop_marginmulti_False_wdecay_0_20_exp_0.96_350_1e-06_0.001_0.001_0.001_lossweights_1.0_1.0'
                print out_dir_train
                # raw_input()

            # if os.path.exists(final_model_file):
            #     print 'skipping',final_model_file
            #     # raw_input()
            #     # continue 
            # else:
            #     print 'not skipping', final_model_file
            #     # raw_input()
            #     # continue

            train_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'.txt')
            test_file = os.path.join(dir_files,type_data,'test_'+str(split_num)+'.txt')
            mean_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'_mean.png')
            std_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'_std.png')


            # train_file = os.path.join('../data/bp4d',type_data,'train_'+str(split_num)+'.txt')
            # test_file = os.path.join('../data/bp4d',type_data,'test_'+str(split_num)+'.txt')

            if model_name.startswith('vgg'):
                mean_std = np.array([[93.5940,104.7624,129.1863],[1.,1.,1.]]) #bgr
                bgr= True
            else:
                # print 'ELSING'
                # mean_std = np.array([[129.1863,104.7624,93.5940],[1.,1.,1.]])
                mean_std = np.array([[0.485*255, 0.456*255, 0.406*255],
                                         [0.229*255, 0.224*255, 0.225*255]])
                # print mean_std
                # raw_input()
                bgr= False
            
            # print mean_std

            # mean_im = scipy.misc.imread(mean_file).astype(np.float32)
            # std_im = scipy.misc.imread(std_file).astype(np.float32)

            class_weights = util.get_class_weights_au(util.readLinesFromFile(train_file))
            data_transforms = {}
            data_transforms['train']= transforms.Compose([
                lambda x: augmenters.random_crop(x,im_size),
                lambda x: augmenters.horizontal_flip(x),
                transforms.ToTensor(),
                lambda x: x*255,
            ])
            data_transforms['val']= transforms.Compose([
                # transforms.ToPILImage(),
                # transforms.Resize((im_size,im_size)),
                # lambda x: augmenters.resize(x,im_size),
                transforms.ToTensor(),
                lambda x: x*255,
            ])

            # data_transforms = {}
            # data_transforms['train']= transforms.Compose([
            #     transforms.ToPILImage(),
            #     # transforms.Resize((im_resize,im_resize)),
            #     transforms.RandomCrop(im_size),
            #     transforms.RandomHorizontalFlip(),
            #     transforms.RandomRotation(15),
            #     transforms.ColorJitter(),
            #     transforms.ToTensor(),
            #     lambda x: x*255,
            #     transforms.Normalize(mean_std[0,:],mean_std[1,:]),
            # ])
            # data_transforms['val']= transforms.Compose([
            #     transforms.ToPILImage(),
            #     transforms.Resize((im_size,im_size)),
            #     transforms.ToTensor(),
            #     lambda x: x*255,
            #     transforms.Normalize(mean_std[0,:],mean_std[1,:]),
            #     ])

            # print train_file
            # print test_file
            # train_data = dataset.Bp4d_Dataset(train_file, bgr = bgr, transform = data_transforms['train'])
            # test_data = dataset.Bp4d_Dataset(test_file, bgr = bgr, transform = data_transforms['val'])
            
            train_data = dataset.Bp4d_Dataset_Mean_Std_Im(train_file, mean_file, std_file, transform = data_transforms['train'],binarize = binarize)
            test_data = dataset.Bp4d_Dataset_Mean_Std_Im(test_file, mean_file, std_file, resize= im_size, transform = data_transforms['val'], binarize = binarize)
        

            network_params = dict(n_classes=n_classes,pool_type='max',r=route_iter,init=init,class_weights = class_weights, reconstruct = reconstruct,loss_weights = loss_weights)
            
            batch_size = 96
            batch_size_val = 96
            
            util.makedirs(out_dir_train)
            

            

            test_params = dict(out_dir_train = out_dir_train,
                        model_num = model_num_curr, 
                        train_data = train_data,
                        test_data = test_data,
                        gpu_id = 0,
                        model_name = model_name,
                        batch_size_val = batch_size_val,
                        criterion = criterion,
                        margin_params = margin_params,
                        network_params = network_params,barebones=True)
            test_model_recon(**test_params)
            # save_visualizations.save_recon_variants(**test_params)
            
        
    # getting_accuracy.print_accuracy(out_dir_meta,pre_pend,strs_append,folds,log='log.txt')



def train_gray(wdecay,lr,route_iter,folds=[4,9],model_name='vgg_capsule_bp4d',epoch_stuff=[30,60],res=False, class_weights = False, reconstruct = False, loss_weights = None,exp=False, disfa = False,vgg_base_file = None,vgg_base_file_str = None, mean_file = None, std_file=None, aug_more = False, align = True):
    out_dirs = []

    out_dir_meta = '../experiments/'+model_name+str(route_iter)
    num_epochs = epoch_stuff[1]
    epoch_start = 0
    if exp:
        dec_after = ['exp',0.96,epoch_stuff[0],1e-6]
    else:
        dec_after = ['step',epoch_stuff[0],0.1]

    lr = lr
    im_resize = 110
    # 256
    im_size = 96
    save_after = 1
    if disfa:
        dir_files = '../data/disfa'
        # type_data = 'train_test_10_6_method_110_gray_align'; n_classes = 10;
        type_data = 'train_test_8_au_all_method_110_gray_align'; n_classes = 8;
        pre_pend = 'disfa_'+type_data+'_'
        binarize = True
    else:
        dir_files = '../data/bp4d'
        if align:
            type_data = 'train_test_files_110_gray_align'; n_classes = 12;
        else:
            type_data = 'train_test_files_110_gray_nodetect'; n_classes = 12;
        pre_pend = 'bp4d_'+type_data+'_'
        binarize = False
            
    criterion = 'marginmulti'
    criterion_str = criterion

    init = False
    aug_str = aug_more
    # if aug_more:
    #     aug_str = 'cropkhAugNoColor'
    # else:
    #     aug_str = 'flipCrop'

    strs_append = '_'+'_'.join([str(val) for val in ['reconstruct',reconstruct,class_weights,aug_str,criterion_str,init,'wdecay',wdecay,num_epochs]+dec_after+lr+['lossweights']+loss_weights+[vgg_base_file_str]])
    
    
    
    
    lr_p=lr[:]
    for split_num in folds:
        
        if res:
            
            # strs_appendc = '_'+'_'.join([str(val) for val in ['reconstruct',reconstruct,True,'flipCrop',criterion_str,init,'wdecay',wdecay,10,'exp',0.96,350,1e-6]+['lossweights']+loss_weights])
            # dec_afterc = dec_after
            strs_appendc = '_'+'_'.join([str(val) for val in ['reconstruct',reconstruct,True,aug_str,criterion_str,init,'wdecay',wdecay,10]+dec_after+lr+['lossweights']+loss_weights+[vgg_base_file_str]])
            
            out_dir_train = os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_appendc)
            model_file = os.path.join(out_dir_train,'model_9.pt')
            epoch_start = 10
            # lr =[0.1*lr_curr for lr_curr in lr_p]

        else:
            model_file = None    


        margin_params = None
        
        out_dir_train =  os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
        final_model_file = os.path.join(out_dir_train,'model_'+str(num_epochs-1)+'.pt')
        if os.path.exists(final_model_file):
            print 'skipping',final_model_file
            # raw_input()
            # continue 
        else:
            print 'not skipping', final_model_file
            # raw_input()
            # continue

        train_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'.txt')
        test_file = os.path.join(dir_files,type_data,'test_'+str(split_num)+'.txt')
        if vgg_base_file is None:
            mean_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'_mean.png')
            std_file = os.path.join(dir_files,type_data,'train_'+str(split_num)+'_std.png')

        print train_file
        print test_file
        print mean_file
        print std_file
        # raw_input()

        class_weights = util.get_class_weights_au(util.readLinesFromFile(train_file))
        
        data_transforms = {}
        if aug_more == 'cropkhAugNoColor':
            train_resize = None
            print 'AUGING MORE'
            list_of_todos = ['flip','rotate','scale_translate']
            
            data_transforms['train']= transforms.Compose([
                lambda x: augmenters.random_crop(x,im_size),
                lambda x: augmenters.augment_image(x,list_of_todos),
                # lambda x: augmenters.horizontal_flip(x),
                transforms.ToTensor(),
                lambda x: x*255,
            ])
        elif aug_more == 'cropFlip':
            train_resize = None
            data_transforms['train']= transforms.Compose([
                lambda x: augmenters.random_crop(x,im_size),
                lambda x: augmenters.horizontal_flip(x),
                transforms.ToTensor(),
                lambda x: x*255,
            ])
        elif aug_more =='NONE':
            train_resize = im_size
            data_transforms['train']= transforms.Compose([
                transforms.ToTensor(),
                lambda x: x*255,
            ])            
        else:
            raise ValueError('aug_more is problematic')

        data_transforms['val']= transforms.Compose([
            transforms.ToTensor(),
            lambda x: x*255,
        ])

        train_data = dataset.Bp4d_Dataset_Mean_Std_Im(train_file, mean_file, std_file, transform = data_transforms['train'], binarize = binarize, resize = train_resize)
        test_data = dataset.Bp4d_Dataset_Mean_Std_Im(test_file, mean_file, std_file, resize= im_size, transform = data_transforms['val'], binarize = binarize)

        # train_data = dataset.Bp4d_Dataset_Mean_Std_Im(test_file, mean_file, std_file, resize= im_size, transform = data_transforms['val'])
        
        network_params = dict(n_classes=n_classes,pool_type='max',r=route_iter,init=init,class_weights = class_weights, reconstruct = reconstruct,loss_weights = loss_weights, vgg_base_file = vgg_base_file)
        
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
                    criterion = criterion,
                    gpu_id = 0,
                    num_workers = 0,
                    model_file = model_file,
                    epoch_start = epoch_start,
                    margin_params = margin_params,
                    network_params = network_params,
                    weight_decay=wdecay)
        test_params = dict(out_dir_train = out_dir_train,
                    model_num = num_epochs-1, 
                    train_data = train_data,
                    test_data = test_data,
                    gpu_id = 0,
                    model_name = model_name,
                    batch_size_val = batch_size_val,
                    criterion = criterion,
                    margin_params = margin_params,
                    network_params = network_params,barebones=True)
        # test_params_train = dict(**test_params)
        # test_params_train['test_data'] = train_data_no_t
        # test_params_train['post_pend'] = '_train'

        print train_params
        param_file = os.path.join(out_dir_train,'params.txt')
        all_lines = []
        for k in train_params.keys():
            str_print = '%s: %s' % (k,train_params[k])
            print str_print
            all_lines.append(str_print)
        util.writeFile(param_file,all_lines)

        # if reconstruct:

        train_model_recon(**train_params)
        test_model_recon(**test_params)
        # test_model_recon(**test_params_train)

        # else:
        #     train_model(**train_params)
        # test_params = dict(out_dir_train = out_dir_train,
        #         model_num = num_epochs-1, 
        #         train_data = train_data,
        #         test_data = test_data,
        #         gpu_id = 0,
        #         model_name = model_name,
        #         batch_size_val = batch_size_val,
        #         criterion = criterion,
        #         margin_params = margin_params,
        #         network_params = network_params)
        # test_model(**test_params)
        
    getting_accuracy.print_accuracy(out_dir_meta,pre_pend,strs_append,folds,log='log.txt')


def train_disfa_ft():
    folds = [0,1]
    # [0,1]
    # range(3)
    model_name = 'khorrami_capsule_7_3_gray'
    disfa = True
    epoch_stuff = [350,10]
    lr = [0.0001,0.001,0.001]
    route_iter = 3

    vgg_base_file = '../experiments/khorrami_capsule_7_3_gray3/bp4d_train_test_files_110_gray_align_0_reconstruct_True_True_flipCrop_marginmulti_False_wdecay_0_10_exp_0.96_350_1e-06_0.001_0.001_0.001_lossweights_1.0_1.0/model_2.pt'
    vgg_base_file_str = 'fold_0_epoch_2_fix_exp_correct_mean'


    vgg_base_file = '../experiments/khorrami_capsule_7_3_gray3/bp4d_train_test_files_110_gray_align_0_reconstruct_True_True_cropkhAugNoColor_marginmulti_False_wdecay_0_10_exp_0.96_350_1e-06_0.001_0.001_0.001_lossweights_1.0_1.0_None/model_9.pt'
    vgg_base_file_str = 'fold_0_epoch_9_moreAug_fix_exp_correct_mean'


    mean_file = '../data/bp4d/train_test_files_110_gray_align/train_0_mean.png'
    std_file =  '../data/bp4d/train_test_files_110_gray_align/train_0_std.png'

    train_gray(0,lr=lr,route_iter = route_iter, folds= folds, model_name= model_name, epoch_stuff=epoch_stuff,res=False, class_weights = True, reconstruct = True, loss_weights = [1.,1.],exp=True, disfa = disfa, vgg_base_file = vgg_base_file,vgg_base_file_str = vgg_base_file_str, mean_file = mean_file, std_file = std_file,aug_more = True)


def ablation_study_rebuttal():
    wdecay = 0
    route_iter = 3
    folds =[2]
    model_name =  'vgg_capsule_7_3' 
    epoch_stuff = [350,1]
    reconstruct = False
    loss_weights = [1.,0.1]
    exp = True
    align = True
    more_aug = 'MORE'
    lr = [0.0001,0.001,0.001]

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug)

def ablation_study_rebuttal_gray():
    wdecay = 0
    lr = [0.001,0.001,0.001]
    loss_weights = [1.0,1.0]
    exp = True
    epoch_stuff = [350,10]
    reconstruct = True
    aug_more = 'NONE'
    folds = [2]
    route_iter = 3
    model_name = 'khorrami_capsule_7_3_gray'
    align = True

    train_gray(wdecay = wdecay,
                lr = lr,
                route_iter = route_iter,
                folds = folds,
                model_name = model_name,
                epoch_stuff = epoch_stuff,
                reconstruct  = reconstruct ,
                loss_weights  = loss_weights ,
                exp = exp,
                aug_more  = aug_more, align = align )


def imagenet_experiments():
    wdecay = 0
    route_iter = 3
    folds =[2]
    model_name =  'vgg_capsule_7_3_imagenet_split_base_do' 
    reconstruct = True
    loss_weights = [1.,0.1]
    
    epoch_stuff = [10,10]
    exp = False
    model_to_test = None
    test_mode = False
    res = False
    # epoch_stuff = [10,10]
    # exp = False

    align = True
    more_aug = 'MORE'
    lr = [1e-5,1e-5,1e-4,1e-4]

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        model_to_test = model_to_test,
        test_mode = test_mode,
        res = res)

def imagenet_vgg_no_ft_resume():
    wdecay = 0
    route_iter = 3
    folds =[2]
    model_name =  'vgg_capsule_7_3_imagenet' 
    reconstruct = True
    loss_weights = [1.,0.1]
    
    # epoch_stuff = [350,5]
    # exp = True

    epoch_stuff = [10,10]
    exp = False
    align = True
    more_aug = 'LESS'
    lr = [0,0.001,0.001]

    print reconstruct
    raw_input()
    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        res = True,
        model_to_test = None)

    # bp4d_256_train_test_files_256_color_align_2_reconstruct_True_False_all_aug_marginmulti_False_wdecay_0_10_step_5_0.1_0_0.001_0.001_LESS_None_lossweights_1.0_0.1

def imagenet_vgg_ft_resume():
    wdecay = 0
    route_iter = 3
    folds =[0,1,2]
    model_name =  'vgg_capsule_7_3_imagenet' 
    reconstruct = True
    loss_weights = [1.,0.1]
    
    # epoch_stuff = [350,5]
    # exp = True

    epoch_stuff = [10,10]
    exp = False
    align = True
    more_aug = 'LESS'
    lr = [0.0001,0.001,0.001]
    res = True

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        res = res)

def face_experiments():
    wdecay = 0
    route_iter = 3
    folds =[2]
    model_name =  'vgg_capsule_7_3_face_split_base_do_70' 
    reconstruct = True
    disfa = False
    loss_weights = [1.,0.1]
    
    epoch_stuff = [5,5]
    exp = False
    model_to_test = None
    # epoch_stuff = [10,10]
    # exp = False
    test_mode = False
    align = True
    more_aug = 'MORE'
    lr = [0,1e-5,1e-4,1e-4]
    res = False

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        model_to_test = model_to_test,
        test_mode = test_mode,
        disfa = disfa,
        res = res
        )

def scratch_color_experiments():
    wdecay = 0
    route_iter = 3
    folds =[0,1,2]
    model_name =  'scratch_architecture_capsule_7_3_color' 
    reconstruct = True
    loss_weights = [1.,1.]
    
    epoch_stuff = [10,10]
    exp = False
    model_to_test = None
    # epoch_stuff = [10,10]
    # exp = False
    test_mode = False
    align = True
    more_aug = 'LESS'
    lr = [1e-4,1e-4,1e-4]

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        model_to_test = model_to_test,
        test_mode = test_mode)

def scratch_color_experiment_disfa():
    wdecay = 0
    route_iter = 3
    folds =[2]
    model_name =  'scratch_architecture_capsule_7_3_color_transfer_conv'
    disfa = True 
    reconstruct = True
    loss_weights = [1.,1.]
    
    epoch_stuff = [5,10]
    res = True
    exp = False
    model_to_test = None
    # epoch_stuff = [10,10]
    # exp = False
    test_mode = False
    align = True
    more_aug = 'LESS'
    lr = [1e-4,1e-4,1e-4]

    train_vgg(wdecay= wdecay,
        lr = lr,
        route_iter = route_iter,
        folds=folds,
        model_name=model_name,
        epoch_stuff=epoch_stuff,
        reconstruct = reconstruct ,
        loss_weights = loss_weights ,
        exp = exp ,
        align = align ,
        more_aug=more_aug,
        model_to_test = model_to_test,
        test_mode = test_mode,
        disfa = disfa,
        res = res)

def temp_scratch():
    dir_model = '../experiments/vgg_face_finetune/bp4d_256_train_test_files_256_color_align_0_False_MultiLabelSoftMarginLoss_10_step_5_0.1_0_0.0001_0.001_0.001_False'
    model_path = os.path.join(dir_model,'model_8.pt')

    dir_model = '../experiments/scratch_architecture_capsule_7_3_color3/bp4d_110_0_reconstruct_True_False_all_aug_marginmulti_False_wdecay_0_10_step_10_0.1_0.0001_0.0001_0.0001_LESS_None_lossweights_1.0_1.0'
    model_path = os.path.join(dir_model,'model_9.pt')

    model =torch.load(model_path).cpu()
    out_file = os.path.join(dir_model,'model_9_just_dict.pt')
    torch.save(model.state_dict(),out_file)
    print out_file

def main():
    # print 'helelei'
    # scratch_color_experiment_disfa()
    # temp_scratch()
    imagenet_experiments()
    # face_experiments()
    # imagenet_experiments()
    # imagenet_vgg_ft_resume()
    # imagenet_vgg_no_ft_resume()
    # imagenet_experiments()
    # ablation_study_rebuttal_gray()





    return



    epoch_stuff = [6,6]
    lr = [0.0001,0.001,0.001]
    route_iter = 3
    folds = [0,1,2]
    # ,1,2]
    model_name = 'vgg_capsule_7_3_with_dropout'
    disfa = False
    loss_weights = None
    # [1.,0.1]
    dropout = 0
    # align = True
    models_to_test = range(6)

    # for idx_model_to_test, model_to_test in enumerate(models_to_test):
        # gpu_id = idx_model_to_test
    train_vgg(0,lr=lr,route_iter = route_iter, folds= folds, model_name= model_name, epoch_stuff=epoch_stuff,res=False, class_weights = True, reconstruct = False, loss_weights = loss_weights, exp = False, align = True, disfa = disfa, more_aug = True, dropout = dropout, model_to_test = None, gpu_id = 0)

    return

    model_name = 'khorrami_capsule_7_3_gray'
    disfa = False
    models_to_test = [2]
    folds = [0,1,2]
    route_iter = 3
    epoch_stuff = [350,15]
    lr = [0.001,0.001,0.001]
    res = True


    # # # model_name = 'khorrami_capsule_7_3_gray'
    # # # disfa = True
    # # # models_to_test = [4]

    train_gray(0,lr=lr,route_iter = route_iter, folds= folds, model_name= model_name, epoch_stuff=epoch_stuff,res=res, class_weights = True, reconstruct = True, loss_weights = [1.,1.],exp=True, disfa = disfa, aug_more= True)

    # save_test_results(0,lr=lr,route_iter = route_iter, folds= folds, model_name= model_name, epoch_stuff=epoch_stuff,res=False, class_weights = True, reconstruct = True, loss_weights = [1.,1.], models_to_test = models_to_test, exp = True, disfa = disfa)



    # meta_data_dir = 'train_test_files_preprocess_maheen_vl_gray'
    # train_khorrami_aug(0,lr=lr,route_iter = route_iter, folds= folds, model_name='khorrami_capsule_7_3', epoch_stuff=epoch_stuff,res=False, class_weights = True, reconstruct = True,oulu= oulu, meta_data_dir = meta_data_dir)




if __name__=='__main__':
    main()