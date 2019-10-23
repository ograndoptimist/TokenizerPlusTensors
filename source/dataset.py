import torch
from itertools import tee
import numpy as np

from source.tensorizer import batchify

from source.utils import build_generator
from source.utils import prepare_generator


class DataIterator(object):
    def __init__(self,
                 data_generator,
                 tokenizer,
                 batch_size,
                 max_len,
                 input_dim,
                 lookup_labels,
                 length):
        self.data_one, self.data_two = tee(data_generator)
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        self.max_len = max_len
        self.input_dim = input_dim
        self.lookup_labels = lookup_labels
        self.length = length

    @property
    def size(self):
        return self.length

    @property
    def steps(self):
        return int(self.length / self.batch_size)

    @staticmethod
    def iter(data,
             batch_size,
             lookup_labels,
             tokenizer,
             max_len):
        sequences = []
        for i, data in zip(range(batch_size), data):
            if i == batch_size:
                break
            label = np.array([lookup_labels[data[1]]], dtype=np.int64)
            if i == 0:
                labels = label
            else:
                labels = np.concatenate((labels, label), 0)
            sequences.append(data[0])
        return batchify(sequences=sequences, max_len=max_len, tokenizer=tokenizer), torch.from_numpy(labels)

    def __iter__(self):
        try:
            yield DataIterator.iter(data=self.data_one, batch_size=self.batch_size,
                                    lookup_labels=self.lookup_labels, tokenizer=self.tokenizer, max_len=self.max_len)
        except UnboundLocalError:
            self.data_one, self.data_two = tee(self.data_two)
            yield DataIterator.iter(data=self.data_one, batch_size=self.batch_size,
                                    lookup_labels=self.lookup_labels, tokenizer=self.tokenizer, max_len=self.max_len)


class Dataset(object):
    def __init__(self,
                 data_generator,
                 tokenizer):
        self.data = data_generator
        self.tokenizer = tokenizer

    def split(self, batch_size, max_len, input_dim, lookup_labels):
        train = []
        test = []
        val = []

        for data in self.data:
            data_block = prepare_generator(data)

            [train.append(_) for _ in data_block[:int(0.7 * len(data_block))]]
            [test.append(_) for _ in data_block[int(0.7 * len(data_block)):int(0.9 * len(data_block))]]
            [val.append(_) for _ in data_block[int(0.9 * len(data_block)):]]

        return DataIterator(data_generator=build_generator(train),
                            tokenizer=self.tokenizer,
                            batch_size=batch_size,
                            max_len=max_len,
                            input_dim=input_dim,
                            lookup_labels=lookup_labels,
                            length=len(train)), \
               DataIterator(data_generator=build_generator(test),
                            tokenizer=self.tokenizer,
                            batch_size=batch_size,
                            max_len=max_len,
                            input_dim=input_dim,
                            lookup_labels=lookup_labels,
                            length=len(test)), \
               DataIterator(data_generator=build_generator(val),
                            tokenizer=self.tokenizer,
                            batch_size=batch_size,
                            max_len=max_len,
                            input_dim=input_dim,
                            lookup_labels=lookup_labels,
                            length=len(val))