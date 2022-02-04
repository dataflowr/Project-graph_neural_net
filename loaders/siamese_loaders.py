from typing import Tuple
import toolbox.maskedtensor as maskedtensor
from torch.utils.data import DataLoader
from toolbox.utils import get_device
#from data_generator import DGL_Loader
import dgl
import torch
from collections.abc import Iterable
from math import sqrt

def collate_fn(samples_list):
    input1_list = [input1 for input1, _ in samples_list]
    input2_list = [input2 for _, input2 in samples_list]
    input1 = maskedtensor.from_list(input1_list, dims=(0, 1), base_name='N')
    input2 = maskedtensor.from_list(input2_list, dims=(0, 1), base_name='M')
    return input1, input2

def _collate_fn_dgl_qap(samples_list):
    input1_list = [input1 for (input1, _),_ in samples_list]
    input2_list = [input2 for (_, input2),_ in samples_list]
    input1_batch = dgl.batch(input1_list)
    input2_batch = dgl.batch(input2_list)
    return ((input1_batch,input2_batch),torch.empty(1))

def _collate_fn_dgl_ne(samples_list):
    bs = len(samples_list)
    input1_list = [input1 for (input1, _) in samples_list]
    target_list = [target for (_,target) in samples_list]
    N,_ = target_list[0].shape
    input_batch = dgl.batch(input1_list)
    target_batch = torch.zeros((bs,N,N))
    for i,target in enumerate(target_list):
        target_batch[i] = target
    return (input_batch,target_batch)

def get_uncollate_function(N,problem):
    def uncollate_function(dgl_out):
        if len(dgl_out.shape)==3:
            dgl_out = dgl_out.squeeze()
        if len(dgl_out.shape)==2:
            fake_N,_ = dgl_out.shape
            bs = int(fake_N//N)
            final_array = torch.zeros((bs,N,N))
            device = get_device(dgl_out)
            final_array = final_array.to(device)
            for i in range(bs):
                final_array[i,:,:] = dgl_out[(i*N):((i+1)*N),(i*N):((i+1)*N)]
        if len(dgl_out.shape)==1: #In this case, the dgl model returns a full list of arrays
            fake_N = dgl_out.shape[0]
            bs = int(fake_N//(N**2))
            final_array = torch.zeros((bs,N,N))
            device = get_device(dgl_out)
            final_array = final_array.to(device)
            for i in range(bs):
                final_array[i,:,:] = dgl_out[(i*(N**2)):((i+1)*(N**2))].reshape((N,N))
        return final_array
    return uncollate_function


def siamese_loader(data, batch_size, constant_n_vertices, use_dgl= False, shuffle=True):
    assert len(data) > 0
    if use_dgl:
        if isinstance(data[0][0],Tuple):
            return DataLoader(data, batch_size=batch_size, shuffle=shuffle,
                                        num_workers=4, collate_fn=_collate_fn_dgl_qap)
        else:
            return DataLoader(data, batch_size=batch_size, shuffle=shuffle,
                                        num_workers=4, collate_fn=_collate_fn_dgl_ne)
    if constant_n_vertices:
        return DataLoader(data, batch_size=batch_size, shuffle=shuffle,
                                        num_workers=4)
    return DataLoader(data, batch_size=batch_size, shuffle=shuffle,
                                    num_workers=0, collate_fn=collate_fn)

def get_loader(use_dgl, data_object: any, batch_size: int, constant_n_vertices: bool=True, shuffle: bool=True, problem=None,**kwargs)->DataLoader:
    """This function creates the appropriate DataLoader depending on the architecture of the problem"""
    if not use_dgl:
        return siamese_loader(data_object, batch_size, constant_n_vertices, use_dgl=False, shuffle=shuffle)
    else:
        return siamese_loader(data_object, batch_size, constant_n_vertices, use_dgl = True, shuffle=shuffle)
    
# if __name__=='__main__':
#     from models.gcn_model import _connectivity_to_dgl_adj
#     N = 50; bs = 16
#     dense_list = [(torch.randn((N,N,2))>0.2).to(float) for _ in range(bs)]
#     dgl_list = [((_connectivity_to_dgl_adj(elt),_connectivity_to_dgl_adj(elt)),None) for elt in dense_list]
#     final_list = _collate_fn_dgl_qap(dgl_list)
#     edge_numbers = [elt.num_edges() for (elt,_),_ in dgl_list]
#     edge = sum(edge_numbers)
#     print(edge)
#     print(final_list)
#     print(final_list[0])
    
    
