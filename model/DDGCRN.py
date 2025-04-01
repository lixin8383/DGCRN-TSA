import math
import torch.nn.functional as F
import torch
import torch.nn as nn
from torch.autograd import Variable
from model.DDGCRNCell import DDGCRNCell
class DGCRM(nn.Module):
    def __init__(self, node_num, dim_in, dim_out, cheb_k, embed_dim, num_layers=1):
        super(DGCRM, self).__init__()
        assert num_layers >= 1, 'At least one DCRNN layer in the Encoder.'
        self.node_num = node_num
        self.input_dim = dim_in
        self.num_layers = num_layers
        self.DGCRM_cells = nn.ModuleList()
        self.DGCRM_cells.append(DDGCRNCell(node_num, dim_in, dim_out, cheb_k, embed_dim))
        for _ in range(1, num_layers):
            self.DGCRM_cells.append(DDGCRNCell(node_num, dim_out, dim_out, cheb_k, embed_dim))

    def forward(self, x, init_state, node_embeddings):

        assert x.shape[2] == self.node_num and x.shape[3] == self.input_dim
        seq_length = x.shape[1]
        current_inputs = x
        output_hidden = []
        for i in range(self.num_layers):
            state = init_state[i]
            inner_states = []
            for t in range(seq_length):
                state = self.DGCRM_cells[i](current_inputs[:, t, :, :], state, [node_embeddings[0][:, t, :, :], node_embeddings[1]])#state=[batch,steps,nodes,input_dim]
                inner_states.append(state)
            output_hidden.append(state)
            current_inputs = torch.stack(inner_states, dim=1)
        return current_inputs, output_hidden

    def init_hidden(self, batch_size):
        init_states = []
        for i in range(self.num_layers):
            init_states.append(self.DGCRM_cells[i].init_hidden_state(batch_size))
        return torch.stack(init_states, dim=0)


class PositionalEncoding(nn.Module):
    def __init__(self, out_dim, max_len=12):
        super(PositionalEncoding, self).__init__()


        pe = torch.zeros(max_len, out_dim)
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, out_dim, 2) *
                             - math.log(10000.0) / out_dim)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).unsqueeze(2)
        self.register_buffer('pe', pe)

    def forward(self, x):

        x = x + Variable(self.pe.to(x.device), requires_grad=False)
        return x


class MultiHeadAttention(nn.Module):
    def __init__(self, embed_size, heads):
        super(MultiHeadAttention, self).__init__()

        self.positional_encoding = PositionalEncoding(embed_size)
        self.embed_size = embed_size
        self.heads = heads

        assert embed_size % heads == 0
        self.head_dim = embed_size // heads

        self.W_V = nn.Linear(self.embed_size, self.head_dim * heads, bias=False)
        self.W_K = nn.Linear(self.embed_size, self.head_dim * heads, bias=False)
        self.W_Q = nn.Linear(self.embed_size, self.head_dim * heads, bias=False)

        self.norm1 = nn.LayerNorm(self.embed_size)
        self.norm2 = nn.LayerNorm(self.embed_size)

        self.fc = nn.Sequential(
            nn.Linear(self.embed_size, self.embed_size),
            nn.ReLU(),
            nn.Linear(self.embed_size, self.embed_size)
        )

    def forward(self, x):

        batch_size, _, _, d_k = x.shape
        x = self.positional_encoding(x).permute(0, 2, 1, 3)

        Q = self.W_Q(x)
        K = self.W_K(x)
        V = self.W_V(x)
        Q = torch.cat(torch.split(Q, self.head_dim, dim=-1), dim=0)
        K = torch.cat(torch.split(K, self.head_dim, dim=-1), dim=0)
        V = torch.cat(torch.split(V, self.head_dim, dim=-1), dim=0)

        scores = torch.matmul(Q, K.transpose(-1, -2)) / torch.sqrt(torch.tensor(d_k, dtype=torch.float))
        attention = F.softmax(scores, dim=-1)
        context = torch.matmul(attention, V)
        context = torch.cat(torch.split(context, batch_size, dim=0), dim=-1)
        context = context + x
        out = self.norm1(context)
        out = self.fc(out) + context
        out = self.norm2(out)
        return out


class DDGCRN(nn.Module):
    def __init__(self, args):
        super(DDGCRN, self).__init__()
        self.num_node = args.num_nodes
        self.input_dim = args.input_dim
        self.hidden_dim = args.rnn_units
        self.output_dim = args.output_dim
        self.horizon = args.horizon
        self.num_layers = args.num_layers
        self.use_D = args.use_day
        self.use_W = args.use_week
        self.dropout1 = nn.Dropout(p=0.1)
        self.dropout2 = nn.Dropout(p=0.1)
        self.default_graph = args.default_graph
        self.node_embeddings1 = nn.Parameter(torch.randn(self.num_node, args.embed_dim), requires_grad=True)
        self.node_embeddings2 = nn.Parameter(torch.randn(self.num_node, args.embed_dim), requires_grad=True)
        self.T_i_D_emb = nn.Parameter(torch.empty(288, args.embed_dim))
        self.D_i_W_emb = nn.Parameter(torch.empty(7, args.embed_dim))

        self.encoder1 = DGCRM(args.num_nodes, args.input_dim, args.rnn_units, args.cheb_k,
                              args.embed_dim, args.num_layers)
        self.encoder2 = DGCRM(args.num_nodes, args.input_dim, args.rnn_units, args.cheb_k,
                              args.embed_dim, args.num_layers)
        #predictor
        self.end_conv1 = nn.Conv2d(1, args.horizon * self.output_dim, kernel_size=(1, self.hidden_dim), bias=True)
        self.end_conv2 = nn.Conv2d(1, args.horizon * self.output_dim, kernel_size=(1, self.hidden_dim), bias=True)
        self.end_conv3 = nn.Conv2d(1, args.horizon * self.output_dim, kernel_size=(1, self.hidden_dim), bias=True)
        self.MultiHeadAttention = MultiHeadAttention(embed_size=self.hidden_dim, heads=4)


    def forward(self, source, i=2):
        node_embedding1 = self.node_embeddings1
        if self.use_D:
            t_i_d_data   = source[..., 1]

            T_i_D_emb = self.T_i_D_emb[(t_i_d_data * 288).type(torch.LongTensor)]
            node_embedding1 = torch.mul(node_embedding1, T_i_D_emb)

        if self.use_W:
            d_i_w_data   = source[..., 2]
            D_i_W_emb = self.D_i_W_emb[(d_i_w_data).type(torch.LongTensor)]
            node_embedding1 = torch.mul(node_embedding1, D_i_W_emb)
        node_embeddings=[node_embedding1,self.node_embeddings1]

        source = source[..., 0].unsqueeze(-1)

        if i == 1:
            init_state1 = self.encoder1.init_hidden(source.shape[0])
            output, _ = self.encoder1(source, init_state1, node_embeddings)
            output = self.dropout1(output[:, -1:, :, :])


            output1 = self.end_conv1(output)
            return output1

        else:
            init_state1 = self.encoder1.init_hidden(source.shape[0])
            output, _ = self.encoder1(source, init_state1, node_embeddings)
            output = self.dropout1(output[:, -1:, :, :])

            output1 = self.end_conv1(output)
            source1 = self.end_conv2(output)

            source2 = source -source1

            init_state2 = self.encoder2.init_hidden(source2.shape[0])
            output2, _ = self.encoder2(source2, init_state2, node_embeddings)
            TAtt = self.MultiHeadAttention(output).permute(0, 2, 1, 3)
            output2 = output2 + TAtt
            output2 = self.dropout2(output2[:, -1:, :, :])
            output2 = self.end_conv3(output2)
            return output1 + output2
