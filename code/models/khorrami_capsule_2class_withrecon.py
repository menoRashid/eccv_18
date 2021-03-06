from torchvision import models
import torch.nn as nn

import numpy as np
import scipy.misc
import torch
from CapsuleLayer import CapsuleLayer
from dynamic_capsules import Dynamic_Capsule_Model_Super
from torch.autograd import Variable
import torch.nn.functional as F
import math

class Khorrami_Capsule_Recon(Dynamic_Capsule_Model_Super):

    def __init__(self,n_classes,loss,in_size = 224, r=3,):
        super(Dynamic_Capsule_Model_Super, self).__init__()
        self.num_classes = n_classes
        self.in_size = in_size
        
        self.reconstruct = True
        self.class_loss = loss

        self.conv_base = []
        self.conv_base.append(nn.Conv2d(1, 32, 5, stride=1))
        self.conv_base.append(nn.ReLU(True))    
        self.conv_base.append(nn.MaxPool2d(2,2))
        
        self.conv_base.append(nn.Conv2d(32, 64, 5, stride=1))
        self.conv_base.append(nn.ReLU(True))
        self.conv_base.append(nn.MaxPool2d(2,2))
        
        self.conv_base.append(nn.Conv2d(64, 128, 5, stride=1))
        self.conv_base.append(nn.ReLU(True))
        # self.conv_base.append(nn.MaxPool2d(2,2))
        

        self.conv_base = nn.Sequential(*self.conv_base)
        
        self.features = []
        self.features.append(CapsuleLayer(32, 1, 128, 8, kernel_size=5, stride=2, num_iterations=r))
        self.features.append(CapsuleLayer(32, 32, 8, 8, kernel_size=7, stride=1, num_iterations=r))
        self.features.append(CapsuleLayer(n_classes, 32, 8, 16, kernel_size=1, stride=1, num_iterations=r))
        self.features = nn.Sequential(*self.features)

        self.reconstruction_loss = nn.MSELoss(size_average=True)
        
        self.decoder = nn.Sequential(
            nn.Linear(16 * self.num_classes, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 1024)
        )
        
        self.upsampler = nn.Upsample(size=(self.in_size,self.in_size), mode='bilinear')

    def forward(self,data, y = None,return_caps = False):
        x = self.conv_base(data)
        # print x.size()
        x = self.features(x)
        # print x.size()
        # raw_input()
        
        x = x.squeeze()
        classes = (x ** 2).sum(dim=-1) ** 0.5
        
        if y is None:
            _, max_length_indices = classes.max(dim=1)
            y = Variable(torch.sparse.torch.eye(self.num_classes)).cuda().index_select(dim=0, index=max_length_indices)
        else:
            y = Variable(torch.sparse.torch.eye(self.num_classes)).cuda().index_select(dim=0, index=y)
        

        # print x.size(),y.size()
        reconstructions = self.decoder((x * y[:, :, None]).view(x.size(0), -1))

        reconstructions = reconstructions.view(reconstructions.size(0),1,int(math.sqrt(reconstructions.size(1))),int(math.sqrt(reconstructions.size(1))))
        # print reconstructions.size()
        reconstructions = self.upsampler(reconstructions)
        
        if return_caps:
            return classes, reconstructions, data, x
        else:
            return classes, reconstructions, data

    def margin_loss(self,classes,labels):
        if self.reconstruct:
            images = classes[2]
            reconstructions = classes[1]
            classes = classes[0]

        class_loss = self.class_loss(classes,labels)

        # spread_loss = spread_loss.sum()

        # if self.reconstruct:
        reconstruction_loss = self.reconstruction_loss(reconstructions, images)
        # print reconstruction_loss
        # print class_loss
        # print class_loss, 0.5*0.001*reconstruction_loss
        # raw_input()
        total_loss = class_loss + 0.5*0.0005*reconstruction_loss
        # /labels.size(0)
            # +  0.00005*reconstruction_loss)/labels.size(0)
            # ) / images.size(0)
        # else:
        #     total_loss = spread_loss
            # / labels.size(0)

        return total_loss


class Network:
    def __init__(self,n_classes,loss,in_size,r, init=False):
        # print 'BN',bn
        model = Khorrami_Capsule_Recon(n_classes,loss,in_size,r)
        
        if init:
            for idx_m,m in enumerate(model.features):
                if isinstance(m, CapsuleLayer):
                    if m.num_in_capsules==1:
                        nn.init.xavier_normal(m.capsules.weight.data)
                        nn.init.constant(m.capsules.bias.data,0.)
                    else:
                        nn.init.normal(m.route_weights.data, mean=0, std=0.1)
                elif isinstance(m,nn.Linear) or isinstance(m,nn.Conv2d):
                    print m
                    nn.init.xavier_normal(m.weight.data)
                    nn.init.constant(m.bias.data,0.)
                
        self.model = model
        
    
    def get_lr_list(self, lr):
        lr_list =[]
        for lr_curr,param_set in zip(lr,[self.model.conv_base,self.model.features,self.model.decoder]):
            if lr_curr==0:
                for param in param_set.parameters():
                    param.requires_grad = False
            else:
                lr_list.append({'params': param_set.parameters(), 'lr': lr_curr})

        # lr_list= [{'params': self.model.conv_base.parameters(), 'lr': lr[0]}] +\
        #         [{'params': self.model.features.parameters(), 'lr': lr[1]}]
        return lr_list

def main():
    import numpy as np
    import torch
    from torch.autograd import Variable
    import torch.optim as optim

    n_classes = 10
    loss = nn.CrossEntropyLoss()
    r = 1
    in_size = 96
    bs=2
    net = Network(n_classes= n_classes, loss = loss, in_size= in_size,r= r, init = False)
    print net.model
    labels = np.random.randn(bs,n_classes)
    labels[labels>0.5]=1
    labels[labels<0.5]=0
    labels = np.zeros(bs)

    net.model = net.model.cuda()
    print net.model
    input = np.random.randn(bs,1,96,96)
    
    input = torch.Tensor(input).cuda()
    print input.shape
    input = Variable(input)
    optimizer = optim.Adam(net.model.parameters(),lr=0.00005)
    labels = Variable(torch.LongTensor(labels).cuda())
    # output = net.model(input)
    # print output.data.shape
    
    # criterion(output,labels)
    epochs = 1000
    for epoch in range(epochs):
        # inputv = Variable(torch.FloatTensor(sample)).view(1, -1)
        # labelsv = Variable(torch.FloatTensor(labels[i])).view(1, -1)
        # print labelsv
        output = net.model(input)
        loss = net.model.margin_loss(output, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        # losses.append(loss.data.mean())
        print('[%d/%d] Loss: %.3f' % (epoch+1, epochs, loss.data))
    print output
    print labels
        

    # criterion = Spread_Loss(50,5)
    # for epoch_num in range(53):
    #     print epoch_num,criterion(output,labels,epoch_num)



if __name__=='__main__':
    main()



