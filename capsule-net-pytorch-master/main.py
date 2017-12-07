"""
PyTorch implementation of CapsNet in Sabour, Hinton et al.'s paper
Dynamic Routing Between Capsules. NIPS 2017.
https://arxiv.org/abs/1710.09829

Usage:
    python main.py
    python main.py --epochs 50
    python main.py --epochs 50 --loss-threshold 0.0001

Author: Cedric Chee
"""

from __future__ import print_function
import argparse

import torch
import torch.optim as optim
from torch.backends import cudnn
from torch.autograd import Variable

import utils
from model import Net


def train(model, data_loader, optimizer, epoch):
    """Train CapsuleNet model on training set
    :param model: The CapsuleNet model
    :param data_loader: An interator over the dataset. It combines a dataset and a sampler
    :optimizer: Optimization algorithm
    :epoch: Current epoch
    :return: Loss
    """
    print('===> Training mode')

    last_loss = None

    # Switch to train mode
    model.train()

    if args.cuda:
        # When we wrap a Module in DataParallel for multi-GPUs
        model = model.module

    for batch_idx, (data, target) in enumerate(data_loader):
        target_one_hot = utils.one_hot_encode(
            target, length=args.num_classes)

        data, target = Variable(data), Variable(target_one_hot)

        if args.cuda:
            data = data.cuda()
            target = target.cuda()

        optimizer.zero_grad()
        output = model(data) # output from DigitCaps (out_digit_caps)
        loss = model.loss(data, output, target) # pass in data for image reconstruction
        loss.backward()
        last_loss = loss.data[0]
        optimizer.step()

        if batch_idx % args.log_interval == 0:
            mesg = 'Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch,
                batch_idx * len(data),
                len(data_loader.dataset),
                100. * batch_idx / len(data_loader),
                loss.data[0])

            print(mesg)

        if last_loss < args.loss_threshold:
            # Stop training early
            break

    return last_loss


def test(model, data_loader):
    """Evaluate model on validation set
    """
    print('===> Evaluate mode')

    # Switch to evaluate mode
    model.eval()

    if args.cuda:
        # When we wrap a Module in DataParallel for multi-GPUs
        model = model.module

    test_loss = 0
    correct = 0
    for data, target in data_loader:
        target_indices = target
        target_one_hot = utils.one_hot_encode(
            target_indices, length=args.num_classes)

        data, target = Variable(data, volatile=True), Variable(target_one_hot)

        if args.cuda:
            data = data.cuda()
            target = target.cuda()

        output = model(data) # output from DigitCaps (out_digit_caps)

        # sum up batch loss
        test_loss += model.loss(data, output, target, size_average=False).data[0] # pass in data for image reconstruction

        # evaluate
        v_magnitud = torch.sqrt((output**2).sum(dim=2, keepdim=True))
        pred = v_magnitud.data.max(1, keepdim=True)[1].cpu()
        correct += pred.eq(target_indices.view_as(pred)).sum()

    test_loss /= len(data_loader.dataset)

    mesg = 'Test set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
        test_loss,
        correct,
        len(data_loader.dataset),
        100. * correct / len(data_loader.dataset))
    print(mesg)


def main():
    """The main function
    Entry point.
    """
    global args

    # Setting the hyper parameters
    parser = argparse.ArgumentParser(description='Example of Capsule Network')
    parser.add_argument('--epochs', type=int, default=10,
                        help='number of training epochs. default=10')
    parser.add_argument('--lr', type=float, default=0.01,
                        help='learning rate. default=0.01')
    parser.add_argument('--batch-size', type=int, default=128,
                        help='training batch size. default=128')
    parser.add_argument('--test-batch-size', type=int,
                        default=128, help='testing batch size. default=128')
    parser.add_argument('--loss-threshold', type=float, default=0.0001,
                        help='stop training if loss goes below this threshold. default=0.0001')
    parser.add_argument('--log-interval', type=int, default=10,
                        help='how many batches to wait before logging training status. default=10')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training. default=false')
    parser.add_argument('--threads', type=int, default=4,
                        help='number of threads for data loader to use. default=4')
    parser.add_argument('--seed', type=int, default=42,
                        help='random seed for training. default=42')
    parser.add_argument('--num-conv-out-channel', type=int, default=256,
                        help='number of channels produced by the convolution. default=256')
    parser.add_argument('--num-conv-in-channel', type=int, default=1,
                        help='number of input channels to the convolution. default=1')
    parser.add_argument('--num-primary-unit', type=int, default=8,
                        help='number of primary unit. default=8')
    parser.add_argument('--primary-unit-size', type=int,
                        default=1152, help='primary unit size is 32 * 6 * 6. default=1152')
    parser.add_argument('--num-classes', type=int, default=10,
                        help='number of digit classes. 1 unit for one MNIST digit. default=10')
    parser.add_argument('--output-unit-size', type=int,
                        default=16, help='output unit size. default=16')
    parser.add_argument('--num-routing', type=int,
                        default=3, help='number of routing iteration. default=3')
    parser.add_argument('--use-reconstruction-loss', action='store_true', default=True,
                        help='use an additional reconstruction loss. default=True')
    parser.add_argument('--regularization-scale', type=float, default=0.0005,
                        help='regularization coefficient for reconstruction loss. default=0.0005')
    parser.add_argument('--is_testing', action='store_true', default=False,
                        help='testing. default=False')
    parser.add_argument('--weights', type=str, default='',
                        help='model file')
    
    args = parser.parse_args()

    print(args)

    # Check GPU or CUDA is available
    args.cuda = not args.no_cuda and torch.cuda.is_available()

    torch.manual_seed(args.seed)
    if args.cuda:
        torch.cuda.manual_seed(args.seed)

    # Load data
    train_loader, test_loader = utils.load_mnist(args)

    # Build Capsule Network
    print('===> Building model')
    model = Net(num_conv_in_channel=args.num_conv_in_channel,
                num_conv_out_channel=args.num_conv_out_channel,
                num_primary_unit=args.num_primary_unit,
                primary_unit_size=args.primary_unit_size,
                num_classes=args.num_classes,
                output_unit_size=args.output_unit_size,
                num_routing=args.num_routing,
                use_reconstruction_loss=args.use_reconstruction_loss,
                regularization_scale=args.regularization_scale,
                cuda_enabled=args.cuda)
    
    print (model)


    # if args.cuda:
    #     print('Utilize GPUs for computation')
    #     print('Number of GPU available', torch.cuda.device_count())
    #     model.cuda()
    #     cudnn.benchmark = True
    #     model = torch.nn.DataParallel(model)
    #     # print (model)
        

    # optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # if not args.is_testing:
    #     # Train and test
    #     for epoch in range(1, args.epochs + 1):
    #         previous_loss = train(model, train_loader, optimizer, epoch)
    #         test(model, test_loader)
    #         utils.checkpoint({
    #             'epoch': epoch + 1,
    #             'state_dict': model.state_dict(),
    #             'optimizer': optimizer.state_dict()
    #         }, epoch)

    #         if previous_loss < args.loss_threshold:
    #             break
    # else:
    #     model.load_state_dict(torch.load(args.weights)['state_dict'])
    #     test(model, test_loader)



if __name__ == "__main__":
    main()
