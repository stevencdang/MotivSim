# Class to support batching of large data for parallel processing


# Modele for methods for performing analytics
# Author: Steven Dang stevencdang.com

import logging

import datetime as dt
import pandas as pd

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class BatchCalculator:
# Batch analytic calculation

    def batch_calc(self, calc, idx, batch_size, calc_args=None):
        #idx is a list of ids
        batches = (idx[i:i+batch_size] for i in range(0, len(idx), batch_size))
        results = []
        for batch in batches:
            if calc_args is None:
                results.append(calc(batch))
            else:
                results.append(calc(batch, *calc_args))
        return pd.concat(results, axis=0)


    def time_calc(self, calc, args):
        start = dt.datetime.now()
        result = calc(*args)
        end = dt.datetime.now()
        runtime = (end - start).total_seconds()
        return result, runtime


    def time_batch(self, calc, idx, batch_size, calc_args=None):
        # Convenience wrapper to time a batch
        args = (calc, idx, batch_size, calc_args)
        result, runtime = self.time_calc(self.batch_calc, args)
        return result, runtime


    def segment_calc(self, calc, segmenter, calc_args=None):
        results = []
        for batch in segmenter.get_batches():
            if calc_args is None:
                results.append(calc(batch))
            else:
                results.append(calc(batch, calc_args))
        return pd.concat(results, axis=0)


class Segmenter:
# Base class to segment an index of data

    def __init__(self, db_col, base_query, lazy=True):
        # The specific database collection that houses the data
        self.db_col = db_col

        # Dictionary defining a Base query defining the base data to segment
        self.base_query = base_query

        # Provide a dataframe to be used as fields to determine segmentation criteria. 
        # index of the dataframe is assumed to be the same as the original data to be segmented
        # self.idx = idx

        self.size = self.db_col.count_documents(base_query)
        logger.debug(f"Segmenting data with {self.size} total documents")

        # Lazy retrieval of data from db
        self.lazy = lazy
        if not lazy:
            self.data = self.get_data()
        else:
            self.data = None
        
        batch_size = self.size/1000
        if batch_size > 1000:
            self.batch_size = 1000
        else:
            self.batch_size = batch_size

            
    def get_data(self):
        # Assumes index of idx is the same as original data
        data = pd.DataFrame(self.db_col.find({"_id": {"$in": self.idx.index.tolist()}}), index="_id")
        return data


    def get_batches(self, idx_fields, batch_size=1):
        # Return a generator function that iterates through subsets of the index
        
        idx = self.get_range(idx_fields) #self.get_collection_range(self.db_col, idx_fields, self.base_query)
        logger.debug(f"got index with: {idx.shape}")
        batch_idx = [idx.iloc[i:i+batch_size, :] for i in range(0, idx.shape[0], batch_size)]
        for batch in batch_idx:
            logger.debug(f"batch index to translate to query: {batch}")
            batch_query = self.df_to_query(batch)
            logger.debug(f"Got query: {str(batch_query)}")
            query, d = self.get_batch_subfields(batch_query)
            logger.debug(f"got batch with size: {d.shape}")
            yield query, d
            
        
    @classmethod
    def df_to_query(cls, df):
        #Iterate through each row
        

        # Express each row as logical AND
        row_queries = []
        for i, row in df.iterrows():
            # logger.debug(f"Translating row {i} of df to query: {str(row)}")
            if len(row.index) > 1:
                qset = []
                for field in row.index:
                    qset.append({f"{field}": row[field]})
                    # logger.debug(f"Added to query: {str(qset)}")
                row_queries.append({"$and": qset})
            else:
                q  = {f"{row.index[0]}": row[0]}
                row_queries.append(q)

        query = {"$or": row_queries}
        return query
        

    @classmethod
    def get_collection_range(cls, db_col, fields, query=None, batch=True, batch_size=100000):
        if query is None:
            query = {}
        if not batch:
            d = pd.DataFrame(db_col.find(query)).loc[:, fields].drop_duplicates()
            return d
        else:
            logger.debug(f"Getting collection range with query: {query}")
            d = db_col.find(query)
            subset = []
            frames = []

            for doc in d:
                logger.debug(f"Got doc: {doc}")
                subset.append(doc)
                if len(subset) == batch_size:
                    logger.debug(f"Forming dataframe from subset with {len(subset)} docs")
                    frames.append(pd.DataFrame(subset).loc[:, fields].drop_duplicates())
                    subset = []

            if len(subset) > 0:
                frames.append(pd.DataFrame(subset).loc[:, fields].drop_duplicates())

            if len(frames) == 0:
                raise Exception(f"No data returned from collection {db_col} with query {query}")
                 
            return pd.concat(frames, axis=0).drop_duplicates()


    def get_range(self, fields):
        idx = self.get_collection_range(self.db_col, fields, self.base_query)
        return idx

    def get_batch_subfields(self, query, fields=None, batch=False, batch_size=100000):
        batch_query = {"$and": [self.base_query, query]}
        if not batch:
            # Return all data
            d = pd.DataFrame(self.db_col.find(query))
            if fields is None:
                return batch_query, d
            else:
                return batch_query, d.loc[:, fields]
        else:
            docs = self.db_col.find(query)
            subset = []
            frames = []

            for doc in docs:
                subset.append(doc)
                if len(subset) == batch_size:
                    frames.append(pd.DataFrame(subset) if fields is None else pd.DataFrame(subset).loc[:, fields])
                    subset = []

            if len(subset) > 0:
                frames.append(pd.DataFrame(subset) if fields is None else pd.DataFrame(subset).loc[:, fields])
                 
            return batch_query, pd.concat(frames, axis=0)


