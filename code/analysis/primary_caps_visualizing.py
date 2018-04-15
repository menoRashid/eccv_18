import sys
sys.path.append('./')
from helpers import util, visualize, receptive_field
import os
import numpy as np
import scipy.misc
import sklearn.metrics
import glob
import multiprocessing
import sklearn.cluster
import sklearn.preprocessing
import sklearn.decomposition
import matplotlib.pyplot as plt

dir_server = '/disk3'
str_replace = ['..',os.path.join(dir_server,'maheen_data/eccv_18')]
click_str = 'http://vision3.idav.ucdavis.edu:1000'


def get_caps_compiled(routed = False):
    

    model_name = 'khorrami_capsule_7_3_bigclass'
    route_iter = 3
    pre_pend = 'ck_96_train_test_files_'
    strs_append = '_reconstruct_True_True_all_aug_margin_False_wdecay_0_600_exp_0.96_350_1e-06_0.001_0.001_0.001'
    model_num = 599
    split_num = 4
    
    out_dir_meta = os.path.join('../experiments',model_name+str(route_iter))
    out_dir_train =  os.path.join(out_dir_meta,pre_pend+str(split_num)+strs_append)
    train_pre =  os.path.join('../data/ck_96','train_test_files')
    test_file =  os.path.join(train_pre,'train_'+str(split_num)+'.txt')

    caps_dir = os.path.join(out_dir_train, 'save_primary_caps_train_data_'+str(model_num))
    # caps_files = glob.glob(os.path.join(caps_dir,'*.npy'))
    caps_files = [os.path.join(caps_dir,str(num)+'.npy') for num in range(10)]
    if routed:
        route_files = [os.path.join(caps_dir,str(num)+'_routes.npy') for num in range(10)]
        routes = []
        for route_file in route_files:
            routes.append(np.load(route_file))
        routes = np.concatenate(routes,1)



    convnet =   [[5,1,2],[2,2,0],[5,1,2],[2,2,0],[7,3,0]]
    imsize = 96

    caps = []
    for caps_file in caps_files:
        caps.append(np.load(caps_file))
    print len(caps)
    print caps[0].shape
    caps = np.concatenate(caps,0)
    print caps.shape
    if routed:
        return caps, test_file, convnet, imsize, routes
    else:
        return caps, test_file, convnet, imsize

def save_ims(mags,filter_num,x,y,test_im,out_dir_curr,convnet,imsize,rewrite = False):
    vec_rel = mags[:,filter_num,x,y]
    print vec_rel.shape
    idx_sort = np.argsort(vec_rel)[::-1]
    print vec_rel[idx_sort[0]]
    print vec_rel[idx_sort[-1]]

    im_row = []
    caption_row =[]
    for idx_idx,idx_curr in enumerate(idx_sort):
        out_file_curr = os.path.join(out_dir_curr,str(idx_idx)+'.jpg')
        if not os.path.exists(out_file_curr) or rewrite:
            im_curr = test_im[idx_curr]
            rec_field, center = receptive_field.get_receptive_field(convnet,imsize,len(convnet)-1, x,y)
            center = [int(round(val)) for val in center]
            range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
            range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
            im_curr = im_curr[range_y[0]:range_y[1],range_x[0]:range_x[1]]
            # print out_file_curr
            # raw_input()
            scipy.misc.imsave(out_file_curr,im_curr)
        im_row.append(out_file_curr)
        caption_row.append('%d %.4f' % (idx_idx,vec_rel[idx_curr]))
    return im_row,caption_row


def k_means(caps,num_clusters, filter_num,x,y,test_im,out_dir_curr,out_file_html,convnet,imsize,rewrite = False):
    vec_rel_org = caps[:,filter_num,x,y,:]
    k_meaner = sklearn.cluster.KMeans(n_clusters=num_clusters)
    vec_rel = sklearn.preprocessing.normalize(vec_rel_org,axis=0) #feature normalize
    vec_rel = vec_rel_org

    bins = k_meaner.fit_predict(vec_rel)
    print bins
    for val in np.unique(bins):
        print val, np.sum(bins==val)

    im_row = [[] for idx in range(num_clusters)]
    caption_row = [[] for idx in range(num_clusters)]
    for idx_idx,bin_curr in enumerate(bins):
        out_file_curr = os.path.join(out_dir_curr,str(idx_idx)+'.jpg')
        # if not os.path.exists(out_file_curr) or rewrite:
        im_curr = test_im[idx_idx]
        rec_field, center = receptive_field.get_receptive_field(convnet,imsize,len(convnet)-1, x,y)
        center = [int(round(val)) for val in center]
        range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
        range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
        im_curr = im_curr[range_y[0]:range_y[1],range_x[0]:range_x[1]]
        # print out_file_curr
        # raw_input()
        scipy.misc.imsave(out_file_curr,im_curr)
        im_row[bin_curr].append(util.getRelPath(out_file_curr,dir_server))
        # print bin_curr,np.linalg.norm(vec_rel_org[idx_idx])
        caption_row[bin_curr].append('%d %.4f' % (bin_curr,np.linalg.norm(vec_rel_org[idx_idx])))

    # out_file_html = out_dir_curr+'.html'
    visualize.writeHTML(out_file_html,im_row,caption_row,40,40)
    print out_file_html
    return im_row, caption_row




def pca(caps,num_clusters, filter_num,x,y,test_im,out_dir_curr,out_file_html,convnet,imsize,rewrite = False):
    vec_rel = caps[:,filter_num,x,y,:]
    # pca = sklearn.decomposition.PCA(n_components=8, whiten = True)
    # vec_rel = sklearn.preprocessing.normalize(vec_rel_org,axis=0) #feature normalize
    # pca.fit(vec_rel_org)
    # print pca.explained_variance_ratio_  , np.sum(pca.explained_variance_ratio_)
    # vec_rel = pca.transform(vec_rel_org)
    # print vec_rel.shape
    im_rows = []
    caption_rows = []
    for vec_curr_idx in range(vec_rel.shape[1]): 
        directions = vec_rel[:,vec_curr_idx]
        # directions = vec_rel/np.linalg.norm(vec_rel,axis=1,keepdims=True)
        # directions = np.arctan(directions[:,0]/directions[:,1])
        # print np.min(directions), np.max(directions)
        idx_sort = np.argsort(directions)

        # print vec_rel.shape
        

        # plt.figure()
        # plt.plot(directions[:,0],directions[:,1],'*b')
        # plt.savefig(out_dir_curr+'.jpg')
        # plt.close()
        # raw_input()

        im_row = []
        # [] for idx in range(num_clusters)]
        caption_row = []
        # [] for idx in range(num_clusters)]
        for idx_idx,idx_curr in enumerate(idx_sort):
            out_file_curr = os.path.join(out_dir_curr,str(idx_idx)+'.jpg')
            # if not os.path.exists(out_file_curr) or rewrite:
            im_curr = test_im[idx_curr]
            rec_field, center = receptive_field.get_receptive_field(convnet,imsize,len(convnet)-1, x,y)
            center = [int(round(val)) for val in center]
            range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
            range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
            im_curr = im_curr[range_y[0]:range_y[1],range_x[0]:range_x[1]]
            # print out_file_curr
            # raw_input()
            scipy.misc.imsave(out_file_curr,im_curr)
            im_row.append(util.getRelPath(out_file_curr,dir_server))
            # [bin_curr].append(util.getRelPath(out_file_curr,dir_server))
            # print bin_curr,np.linalg.norm(vec_rel_org[idx_idx])
            caption_row.append('%d %.2f' % (idx_curr,directions[idx_curr]))

        im_rows.append(im_row)
        caption_rows.append(caption_row)
    # out_file_html = out_dir_curr+'.html'
    visualize.writeHTML(out_file_html,im_rows,caption_rows,40,40)
    print out_file_html


    # k_meaner = sklearn.cluster.KMeans(n_clusters=num_clusters)
    # vec_rel = sklearn.preprocessing.normalize(vec_rel_org,axis=0) #feature normalize
    # vec_rel = vec_rel_org

    # bins = k_meaner.fit_predict(vec_rel)
    # print bins
    # for val in np.unique(bins):
    #     print val, np.sum(bins==val)

    # im_row = [[] for idx in range(num_clusters)]
    # caption_row = [[] for idx in range(num_clusters)]
    # for idx_idx,bin_curr in enumerate(bins):
    #     out_file_curr = os.path.join(out_dir_curr,str(idx_idx)+'.jpg')
    #     # if not os.path.exists(out_file_curr) or rewrite:
    #     im_curr = test_im[idx_idx]
    #     rec_field, center = receptive_field.get_receptive_field(convnet,imsize,len(convnet)-1, x,y)
    #     center = [int(round(val)) for val in center]
    #     range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
    #     range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
    #     im_curr = im_curr[range_y[0]:range_y[1],range_x[0]:range_x[1]]
    #     # print out_file_curr
    #     # raw_input()
    #     scipy.misc.imsave(out_file_curr,im_curr)
    #     im_row[bin_curr].append(util.getRelPath(out_file_curr,dir_server))
    #     # print bin_curr,np.linalg.norm(vec_rel_org[idx_idx])
    #     caption_row[bin_curr].append('%d %.4f' % (bin_curr,np.linalg.norm(vec_rel_org[idx_idx])))

    # # out_file_html = out_dir_curr+'.html'
    # visualize.writeHTML(out_file_html,im_row,caption_row,40,40)
    # print out_file_html
    # return im_row, caption_row

    



def script_viz_k_means():
    out_dir_htmls = '../experiments/figures/primary_caps_viz_pca'.replace(str_replace[0],str_replace[1])
    util.mkdir(out_dir_htmls)
    out_dir_im = os.path.join(out_dir_htmls,'im')
    util.mkdir(out_dir_im)


    caps, test_file, convnet, imsize  = get_caps_compiled()
    num_clusters = 32


    # arr_vals = [(x,y,filter_num) for x in range(6) for y in range(6) for filter_num in range(32)]
    arr_vals = [(x,y,filter_num) for x in [3] for y in [5] for filter_num in [3]]

    test_im = [scipy.misc.imread(line_curr.split(' ')[0]) for line_curr in util.readLinesFromFile(test_file)]
    print len(test_im)
    print test_im[0].shape

    for x,y,filter_num in arr_vals:
        out_dir_curr = os.path.join(out_dir_im,str(x)+'_'+str(y)+'_'+str(filter_num))
        util.mkdir(out_dir_curr)
        out_file_html = os.path.join(out_dir_htmls,str(x)+'_'+str(y)+'_'+str(filter_num)+'.html')
        # if os.path.exists(out_file_html):
        #     continue
        pca(caps,num_clusters, filter_num,x,y,test_im,out_dir_curr,out_file_html,convnet,imsize,rewrite = False)
        # break
    visualize.writeHTMLForFolder(out_dir_im)


def script_viz_mag():
    
    out_dir_htmls = '../experiments/figures/primary_caps_viz'.replace(str_replace[0],str_replace[1])
    util.mkdir(out_dir_htmls)
    out_dir_im = os.path.join(out_dir_htmls,'im')
    util.mkdir(out_dir_im)

    caps, test_file, convnet, imsize  = get_caps_compiled()
    mags = np.linalg.norm(caps,  axis = 4)
    print mags.shape
    print np.min(mags), np.max(mags)

    test_im = [scipy.misc.imread(line_curr.split(' ')[0]) for line_curr in util.readLinesFromFile(test_file)]
    print len(test_im)
    print test_im[0].shape

    for x in range(mags.shape[2]):
            for y in range(mags.shape[3]):
                out_file_html = os.path.join(out_dir_htmls,str(x)+'_'+str(y)+'.html')
                ims_html = []
                captions_html = []

                for filter_num in range(mags.shape[1]):
                    out_dir_curr = os.path.join(out_dir_im,str(x)+'_'+str(y)+'_'+str(filter_num))
                    util.mkdir(out_dir_curr)
                
                    im_row,caption_row = save_ims(mags,filter_num,x,y,test_im,out_dir_curr, convnet, imsize)
                    im_row = [util.getRelPath(im_curr,dir_server) for im_curr in im_row]
                    # caption_row = [os.path.split(im_curr)[1][:-4] for im_curr in im_row]
                    ims_html.append(im_row[:10]+im_row[-10:])
                    captions_html.append(caption_row[:10]+caption_row[-10:])

                visualize.writeHTML(out_file_html,ims_html,captions_html,40,40)

def save_all_patches():
    out_dir = '../experiments/figures/primary_caps_viz/im_all_patches/train'
    util.makedirs(out_dir)
    _, test_file, convnet, imsize  = get_caps_compiled()
    test_im = [scipy.misc.imread(line_curr.split(' ')[0]) for line_curr in util.readLinesFromFile(test_file)]

    for idx_test_im_curr,im_curr in enumerate(test_im):
        for x in range(6):
            for y in range(6):

                out_file_curr = os.path.join(out_dir,'_'.join([str(val) for val in [idx_test_im_curr,x,y]])+'.jpg')
                print out_file_curr
                rec_field, center = receptive_field.get_receptive_field(convnet,imsize,len(convnet)-1, x,y)
                center = [int(round(val)) for val in center]
                range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
                range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
                patch = im_curr[range_y[0]:range_y[1],range_x[0]:range_x[1]]
                # print out_file_curr
                # raw_input()
                scipy.misc.imsave(out_file_curr,patch)



def script_view_all_patches_sorted():

    out_dir_meta = '../experiments/figures/primary_caps_viz'.replace(str_replace[0],str_replace[1])
    out_dir_im = os.path.join(out_dir_meta,'im_all_patches/train')

    caps, test_file, convnet, imsize  = get_caps_compiled(routed= False)
    mags = np.linalg.norm(caps,axis = 4)

    mags_org = mags
    print 'mags_org.shape',mags_org.shape

    mags = np.transpose(mags,(0,2,3,1))
    print mags.shape
    mags = np.reshape(mags,(mags.shape[0]*mags.shape[1]*mags.shape[2],mags.shape[3]))
    print mags.shape
    idx_helper = range(mags.shape[0])
    print len(idx_helper)
    idx_helper = np.reshape(idx_helper,(caps.shape[0],caps.shape[2],caps.shape[3]))
    print idx_helper.shape


    num_to_keep = 100
    print 'mags_org.shape',mags_org.shape


    out_file_html = os.path.join(out_dir_meta,'mag_sorted.html')

    im_rows = []
    caption_rows = []

    for filt_num in range(mags.shape[1]):
        im_row = []
        caption_row =[]
        mag_curr = mags[:,filt_num]
        print np.min(mag_curr), np.max(mag_curr)
        idx_sort = list(np.argsort(mag_curr)[::-1])
        idx_sort = idx_sort[:num_to_keep]+idx_sort[-num_to_keep:]

        sorted_mag_curr = mag_curr[idx_sort]
        # print sorted_mag_curr[0],sorted_mag_curr[-1]
        # raw_input()
        

        for idx_idx, idx_curr in enumerate(idx_sort):
            arg_multi_dim = np.where(idx_helper==idx_curr)
            arg_multi_dim = [arr[0] for arr in arg_multi_dim]
            # print arg_multi_dim
            # if arg_multi_dim[1]==0 or arg_multi_dim[1]==5 or arg_multi_dim[2]==0 or arg_multi_dim[2]==5:
            #     continue
            # arg_multi_dim = [arg_multi_dim[0],max(arg_multi_dim[2],1),max(arg_multi_dim[1],1)]
            file_curr = os.path.join(out_dir_im,'_'.join([str(val) for val in arg_multi_dim])+'.jpg')
            assert os.path.exists(file_curr)
            im_row.append(util.getRelPath(file_curr,dir_server))
            caption_row.append('%d %.4f' % (idx_idx, sorted_mag_curr[idx_idx]))
            # if len(im_row)==num_to_keep:
            #     break
        im_rows.append(im_row)
        caption_rows.append(caption_row)

    visualize.writeHTML(out_file_html,im_rows,caption_rows,40,40)
    print out_file_html.replace(dir_server,click_str)

def script_view_clusters(routed = False,mag_sorted = True):
    out_dir_meta = '../experiments/figures/primary_caps_viz'.replace(str_replace[0],str_replace[1])
    out_dir_im = os.path.join(out_dir_meta,'im_all_patches/train')
    
    out_dir_meta = '../experiments/figures/primary_caps_viz_clusters'.replace(str_replace[0],str_replace[1])
    util.mkdir(out_dir_meta)

    caps, test_file, convnet, imsize, routes  = get_caps_compiled(routed= True)
    mags = np.linalg.norm(caps,axis = 4)
    mags_org = mags
    # print 'mags_org.shape',mags_org.shape
    mags = np.transpose(mags,(0,2,3,1))
    # print mags.shape
    mags = np.reshape(mags,(mags.shape[0]*mags.shape[1]*mags.shape[2],mags.shape[3]))
    # print mags.shape

    
    # print routes.shape

    # print test_file
    gt_class = [int(line_curr.split(' ')[1]) for line_curr in util.readLinesFromFile(test_file)]

    routes_gt = routes[gt_class,range(routes.shape[1])].squeeze()
    mag_routes = np.linalg.norm(routes_gt,axis = 2)
    # np.sum(routes_gt,axis=2)
    # 
    mag_routes = np.reshape(mag_routes,(mag_routes.shape[0],32,6,6,1))
    
    # print np.min(mag_routes),np.max(mag_routes)
    # print mag_routes.shape
    # print caps.shape
    if routed:
        caps = caps*mag_routes


    caps_org = np.array(caps)

    caps = np.transpose(caps,(0,2,3,1,4))
    # print caps.shape
    caps = np.reshape(caps,(caps.shape[0]*caps.shape[1]*caps.shape[2],caps.shape[3],caps.shape[4]))
    # print caps.shape
    # print mags.shape
    idx_helper = range(caps.shape[0])
    # print len(idx_helper)
    idx_helper = np.reshape(idx_helper,(caps_org.shape[0],caps_org.shape[2],caps_org.shape[3]))
    # print idx_helper.shape


    num_to_keep = 100
    num_clusters = 32

    for filt_num in range(caps.shape[1]):
        if mag_sorted:
            out_file_html = os.path.join(out_dir_meta,str(filt_num)+'_mag_sorted.html')
        elif routed:
            out_file_html = os.path.join(out_dir_meta,str(filt_num)+'_route_weighted.html')
        else:
            out_file_html = os.path.join(out_dir_meta,str(filt_num)+'.html')
            
        im_rows = []
        caption_rows = []
        
        caps_curr = caps[:,filt_num]    
        mags_curr = mags[:,filt_num]

        k_meaner = sklearn.cluster.KMeans(n_clusters=num_clusters)
        vec_rel = sklearn.preprocessing.normalize(caps_curr,axis = 1)
        # sklearn.preprocessing.normalize(sklearn.preprocessing.normalize(caps_curr,axis=0),axis=1) #feature normalize
        # print 'vec_rel.shape',vec_rel.shape
        print vec_rel.shape
        # numpy.random.permutation(x)
        k_meaner.fit(np.random.permutation(vec_rel))
        cluster_centers = k_meaner.cluster_centers_
        print cluster_centers.shape
        cluster_belongings = k_meaner.predict(vec_rel)
        # print cluster_centers,cluster_centers.shape

        for idx_cluster_center,cluster_center in enumerate(cluster_centers):
            if mag_sorted:
                idx_rel = np.where(cluster_belongings == idx_cluster_center)[0]
                # print idx_rel.shape
                # print idx_rel[:10]
                mag_rel = mags_curr[idx_rel]
                idx_sort = np.argsort(mag_rel)[::-1]
                idx_sort = list(idx_rel[idx_sort])
                # print idx_sort[:10]
                # raw_input()
            else:            
                cluster_center = cluster_center[np.newaxis,:]
                # print (vec_rel-cluster_center).shape
                dist = np.linalg.norm(vec_rel-cluster_center,axis = 1)
                # print dist.shape
                # print mags.shape
                # raw_input()
                idx_sort = list(np.argsort(dist))

            idx_sort = idx_sort[:num_to_keep]+idx_sort[-num_to_keep:]

            im_row = []
            caption_row =[]

            for idx_idx, idx_curr in enumerate(idx_sort):
                arg_multi_dim = np.where(idx_helper==idx_curr)
                arg_multi_dim = [arr[0] for arr in arg_multi_dim]
                
                file_curr = os.path.join(out_dir_im,'_'.join([str(val) for val in arg_multi_dim])+'.jpg')
                assert os.path.exists(file_curr)
                im_row.append(util.getRelPath(file_curr,dir_server))
                caption_row.append('%d %.4f' %(idx_idx,mags_curr[idx_curr]))
                    # str(idx_idx)+' '+str(filt_num))
                
            im_rows.append(im_row)
            caption_rows.append(caption_row)

        visualize.writeHTML(out_file_html,im_rows,caption_rows,40,40)
        print out_file_html.replace(dir_server,click_str)
        # break

    #         print cluster_center.shape

    #         raw_input()

            
    #     im_row = []
    #     caption_row =[]
    
    #     print caps_curr.shape
    #     raw_input()
    #     print np.min(mag_curr), np.max(mag_curr)
    #     idx_sort = list(np.argsort(mag_curr)[::-1])
    #     idx_sort = idx_sort[:num_to_keep]+idx_sort[-num_to_keep:]

    #     sorted_mag_curr = mag_curr[idx_sort]
    #     # print sorted_mag_curr[0],sorted_mag_curr[-1]
    #     # raw_input()
        

    #     for idx_idx, idx_curr in enumerate(idx_sort):
    #         arg_multi_dim = np.where(idx_helper==idx_curr)
    #         arg_multi_dim = [arr[0] for arr in arg_multi_dim]
    #         # print arg_multi_dim
    #         # if arg_multi_dim[1]==0 or arg_multi_dim[1]==5 or arg_multi_dim[2]==0 or arg_multi_dim[2]==5:
    #         #     continue
    #         # arg_multi_dim = [arg_multi_dim[0],max(arg_multi_dim[2],1),max(arg_multi_dim[1],1)]
    #         file_curr = os.path.join(out_dir_im,'_'.join([str(val) for val in arg_multi_dim])+'.jpg')
    #         assert os.path.exists(file_curr)
    #         im_row.append(util.getRelPath(file_curr,dir_server))
    #         caption_row.append(str(idx_idx)+' '+str(filt_num))
    #         # if len(im_row)==num_to_keep:
    #         #     break
    #     im_rows.append(im_row)
    #     caption_rows.append(caption_row)

    # visualize.writeHTML(out_file_html,im_rows,caption_rows,40,40)
    # print out_file_html.replace(dir_server,click_str)

def script_view_route_weighted_patches_sorted():
    out_dir_meta = '../experiments/figures/primary_caps_viz'.replace(str_replace[0],str_replace[1])
    out_dir_im = os.path.join(out_dir_meta,'im_all_patches/train')

    caps, test_file, convnet, imsize, routes  = get_caps_compiled(routed= True)
    
    print routes.shape

    print test_file
    gt_class = [int(line_curr.split(' ')[1]) for line_curr in util.readLinesFromFile(test_file)]

    routes_gt = routes[gt_class,range(routes.shape[1])].squeeze()
    mag_routes = np.linalg.norm(routes_gt,axis = 2)
    # np.sum(routes_gt,axis=2)
    # 
    mag_routes = np.reshape(mag_routes,(mag_routes.shape[0],32,6,6,1))
    
    print np.min(mag_routes),np.max(mag_routes)
    print mag_routes.shape
    print caps.shape
    
    caps = caps*mag_routes

    mags = np.linalg.norm(caps,axis = 4)
    # mags = mags*mag_routes

    mags_org = mags
    print 'mags_org.shape',mags_org.shape

    
    mags = np.transpose(mags,(0,2,3,1))
    print mags.shape
    mags = np.reshape(mags,(mags.shape[0]*mags.shape[1]*mags.shape[2],mags.shape[3]))
    print mags.shape
    idx_helper = range(mags.shape[0])
    print len(idx_helper)
    idx_helper = np.reshape(idx_helper,(caps.shape[0],caps.shape[2],caps.shape[3]))
    print idx_helper.shape


    num_to_keep = 100
    print 'mags_org.shape',mags_org.shape


    out_file_html = os.path.join(out_dir_meta,'mag_sorted_route_weighted.html')

    im_rows = []
    caption_rows = []

    for filt_num in range(mags.shape[1]):
        im_row = []
        caption_row =[]
        mag_curr = mags[:,filt_num]
        print np.min(mag_curr), np.max(mag_curr)
        idx_sort = list(np.argsort(mag_curr)[::-1])
        idx_sort = idx_sort[:num_to_keep]+idx_sort[-num_to_keep:]

        sorted_mag_curr = mag_curr[idx_sort]
        # print sorted_mag_curr[0],sorted_mag_curr[-1]
        # raw_input()
        

        for idx_idx, idx_curr in enumerate(idx_sort):
            arg_multi_dim = np.where(idx_helper==idx_curr)
            arg_multi_dim = [arr[0] for arr in arg_multi_dim]
            # print arg_multi_dim
            # if arg_multi_dim[1]==0 or arg_multi_dim[1]==5 or arg_multi_dim[2]==0 or arg_multi_dim[2]==5:
            #     continue
            # arg_multi_dim = [arg_multi_dim[0],max(arg_multi_dim[2],1),max(arg_multi_dim[1],1)]
            file_curr = os.path.join(out_dir_im,'_'.join([str(val) for val in arg_multi_dim])+'.jpg')
            assert os.path.exists(file_curr)
            im_row.append(util.getRelPath(file_curr,dir_server))
            caption_row.append(str(idx_idx)+' '+str(filt_num))
            # if len(im_row)==num_to_keep:
            #     break
        im_rows.append(im_row)
        caption_rows.append(caption_row)

    visualize.writeHTML(out_file_html,im_rows,caption_rows,40,40)
    print out_file_html.replace(dir_server,click_str)


def main():
    script_view_clusters(routed = False,mag_sorted = True)
    # script_view_all_patches_sorted()
    # script_view_route_weighted_clusters()
    # script_view_route_weighted_clusters()

    
    # script_viz_mag()
    # script_viz_k_means()





    # for x in range(6):
    #     for y in range(6):
    #         rec_field, center = receptive_field.get_receptive_field(convnet,imsize,4, x,y)
    #         center = [int(round(val)) for val in center]
    #         range_x = [max(0,center[0]-rec_field/2),min(imsize,center[0]+rec_field/2)]
    #         range_y = [max(0,center[1]-rec_field/2),min(imsize,center[1]+rec_field/2)]
    #         print x, y , range_x, range_y


if __name__=='__main__':
    main()