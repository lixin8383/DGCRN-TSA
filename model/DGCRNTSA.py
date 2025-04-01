import torch
import torch.nn.functional as F
import torch.nn as nn
import numpy as np
from collections import OrderedDict

class DGCN(nn.Module):
    def __init__(self, dim_in, dim_out, cheb_k, embed_dim):
        super(DGCN, self).__init__()
        self.cheb_k = cheb_k
        self.weights_pool = nn.Parameter(torch.FloatTensor(embed_dim, cheb_k, dim_in, dim_out))
        self.weights = nn.Parameter(torch.FloatTensor(cheb_k,dim_in, dim_out))
        self.bias_pool = nn.Parameter(torch.FloatTensor(embed_dim, dim_out))
        self.bias = nn.Parameter(torch.FloatTensor(dim_out))
        self.hyperGNN_dim = 16
        self.middle_dim = 2
        self.embed_dim = embed_dim
        self.fc=nn.Sequential(
                OrderedDict([('fc1', nn.Linear(dim_in, self.hyperGNN_dim)),
                             ('sigmoid1', nn.Sigmoid()),
                             ('fc2', nn.Linear(self.hyperGNN_dim, self.middle_dim)),
                             ('sigmoid2', nn.Sigmoid()),
                             ('fc3', nn.Linear(self.middle_dim, self.embed_dim))]))
    def forward(self, x, node_embeddings):
        #x shaped[B, N, C], node_embeddings shaped [N, D] -> supports shaped [N, N]
        #output shape [B, N, C]
        node_num = node_embeddings[0].shape[1]
        supports1 = torch.eye(node_num).to(node_embeddings[0].device)
        filter = self.fc(x)
        nodevec = torch.tanh(torch.mul(node_embeddings[0], filter))  #[B,N,dim_in]
        supports2 = DGCN.get_laplacian(F.relu(torch.matmul(nodevec, nodevec.transpose(2, 1))), supports1)

        x_g1 = torch.einsum("nm,bmc->bnc", supports1, x)
        x_g2 = torch.einsum("bnm,bmc->bnc", supports2, x)
        x_g = torch.stack([x_g1,x_g2],dim=1)

        weights = torch.einsum('nd,dkio->nkio', node_embeddings[1], self.weights_pool)                                                                                #[N, cheb_k, dim_in, dim_out]=[nodes,cheb_k,hidden_size,output_dim]
        bias = torch.matmul(node_embeddings[1], self.bias_pool) #N, dim_out             #[che_k,nodes,nodes]* [batch,nodes,dim_in]=[B, cheb_k, N, dim_in]
        x_g = x_g.permute(0, 2, 1, 3)  # B, N, cheb_k, dim_in
        x_gconv = torch.einsum('bnki,nkio->bno', x_g, weights) + bias  #b, N, dim_out

        return x_gconv

    @staticmethod
    def get_laplacian(graph, I, normalize=True):
        if normalize:
            D = torch.diag_embed(torch.sum(graph, dim=-1) ** (-1 / 2))
            L = torch.matmul(torch.matmul(D, graph), D)
        else:
            graph = graph + I
            D = torch.diag_embed(torch.sum(graph, dim=-1) ** (-1 / 2))
            L = torch.matmul(torch.matmul(D, graph), D)
        return L
