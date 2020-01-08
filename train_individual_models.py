"""
Version of the model where we are training to generate specific emails from members in the email chain.

samples are single emails from the person.

We will cache pre-tokenized versions of this data

"""
import glob
import os
import pickle

import torch


class SingleDataset(torch.utils.data.Dataset):
    def __init__(self, dirpath: str, tokenizer, args):
        """
        Assumes that directorypath is directory of a single person's emails, stored as individual text files

        :param dirpath: path to directory containing emails.
        """
        cached_filepath = os.path.join(dirpath, "_cached_")
        if os.path.exists(cached_filepath) and not args.overwrite:
            with open(cached_filepath, 'rb') as fin:
                self.samples = pickle.load(fin)
        else:
            text_files = glob.glob(dirpath + "/*.txt")
            assert text_files
            self.samples = [tokenizer(x) for x in text_files]
            with open(cached_filepath, 'wb') as fout:
                pickle.dump(self.samples, fout)


    def __len__(self):
        return len(self.samples)

    def __getitem__(self, item):
        return torch.tensor(self.samples[item])

