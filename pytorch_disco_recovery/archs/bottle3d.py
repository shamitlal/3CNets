import torch
import torch.nn as nn
import time
# import hyperparams as hyp
# from utils_basic import *
import torch.nn.functional as F

class Bottle3d(nn.Module):
    def __init__(self, in_channel, pred_dim, chans=64):
        super(Bottle3d, self).__init__()
        conv3d = []

        # self.out_chans = [chans, 2*chans, 4*chans, 8*chans, 16*chans]
        # self.out_chans = [chans, 2*chans, 4*chans, 8*chans]
        self.out_chans = [chans, 2*chans, 4*chans]
        
        n_layers = len(self.out_chans)
        
        for i in list(range(n_layers)):
            if i==0:
                in_dim = in_channel
            else:
                in_dim = self.out_chans[i-1]
            out_dim = self.out_chans[i]
            conv3d.append(nn.Sequential(
                nn.Conv3d(in_channels=in_dim, out_channels=out_dim, kernel_size=4, stride=2, padding=0),
                nn.LeakyReLU(),
                nn.BatchNorm3d(num_features=out_dim),
            ))
        self.conv3d = nn.ModuleList(conv3d)

        hidden_dim = 1024
        self.linear_layers = nn.Sequential(
            nn.Linear(self.out_chans[-1]*2*2*2, hidden_dim),
            nn.LeakyReLU(),
            nn.Linear(hidden_dim, pred_dim),
        )
        
    def forward(self, feat):
        B, C, Z, Y, X = list(feat.shape)
        # print(feat.shape)
        for conv3d_layer in self.conv3d:
            feat = conv3d_layer(feat)
            # print('bottle', feat.shape)
        feat = feat.reshape(B, -1)
        # print('bottle', feat.shape)
        # feat = self.linear_layers(feat)
        return feat

class ResNetBottle3d(nn.Module):
    def __init__(self, in_dim, mid_dim, out_dim, resolution=64):
        super(ResNetBottle3d, self).__init__()
        # first lqyer - downsampling
        ksize, stride, padding = 4, 2, 1
        self.down_sampler0 = nn.Sequential(
            nn.Conv3d(in_channels=in_dim, out_channels=mid_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(num_features=mid_dim),
            nn.LeakyReLU(),
        )

        ksize, stride, padding = 3, 1, 1
        self.res_block1 = self.generate_block(mid_dim, mid_dim, ksize, stride, padding)
        self.res_block2 = self.generate_block(mid_dim, mid_dim, ksize, stride, padding)
        self.res_block3 = self.generate_block(mid_dim, mid_dim, ksize, stride, padding)
        # self.res_block4 = self.generate_block(mid_dim, mid_dim, ksize, stride, padding)

        self.down_sampler1 = nn.Sequential(
            nn.Conv3d(in_channels=mid_dim, out_channels=mid_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(num_features=mid_dim),
            nn.LeakyReLU(),
        )
        self.down_sampler2 = nn.Sequential(
            nn.Conv3d(in_channels=mid_dim, out_channels=mid_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(num_features=mid_dim),
            nn.LeakyReLU(),
        )
        self.down_sampler3 = nn.Sequential(
            nn.Conv3d(in_channels=mid_dim, out_channels=mid_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm3d(num_features=mid_dim),
            nn.LeakyReLU(),
        )
        # self.down_sampler4 = nn.Sequential(
        #     nn.Conv3d(in_channels=mid_dim, out_channels=mid_dim, kernel_size=4, stride=2, padding=1),
        #     nn.BatchNorm3d(num_features=mid_dim),
        #     nn.LeakyReLU(),
        # )

        self.lrelu = nn.LeakyReLU()

        # # final 1x1x1 conv to get our desired pred_dim
        # self.final_feature = nn.Conv3d(in_channels=chans, out_channels=pred_dim, kernel_size=1, stride=1, padding=0)

        self.linear_layers = nn.Sequential(
            nn.Linear(mid_dim*int((resolution/2/2/2/2)**3), mid_dim*2),
            # nn.Linear(mid_dim*int((resolution/2/2/2/2/2)**3), mid_dim*2),
            nn.LeakyReLU(),
            nn.Linear(mid_dim*2, out_dim),
        )

    def generate_block(self, in_dim, out_dim, ksize, stride, padding):
        block = nn.Sequential(
            nn.Conv3d(in_channels=in_dim, out_channels=out_dim, kernel_size=1, stride=1),
            nn.BatchNorm3d(num_features=out_dim),
            nn.LeakyReLU(),
            nn.Conv3d(in_channels=in_dim, out_channels=out_dim, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm3d(num_features=out_dim),
            nn.LeakyReLU(),
            nn.Conv3d(in_channels=in_dim, out_channels=out_dim, kernel_size=1, stride=1),
            nn.BatchNorm3d(num_features=out_dim),
            )
        return block

    def forward(self, feat):
        B, C, Z, Y, X = list(feat.shape)
        print(feat.shape)
        
        feat = self.down_sampler0(feat)
        print(feat.shape)

        feat_before = feat
        feat_after = self.res_block1(feat)
        feat = feat_before + feat_after
        feat = self.lrelu(feat)
        feat = self.down_sampler1(feat)
        print(feat.shape)

        feat_before = feat
        feat_after = self.res_block2(feat)
        feat = feat_before + feat_after
        feat = self.lrelu(feat)
        feat = self.down_sampler2(feat)
        print(feat.shape)

        feat_before = feat
        feat_after = self.res_block3(feat)
        feat = feat_before + feat_after
        feat = self.lrelu(feat)
        feat = self.down_sampler3(feat)
        print(feat.shape)

        # feat_before = feat
        # feat_after = self.res_block4(feat)
        # feat = feat_before + feat_after
        # feat = self.lrelu(feat)
        # feat = self.down_sampler4(feat)
        # print(feat.shape)

        feat = feat.reshape(B, -1)
        feat = self.linear_layers(feat)
        print(feat.shape)

        return feat
    
