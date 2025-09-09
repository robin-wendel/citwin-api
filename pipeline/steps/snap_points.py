import numpy as np
from sklearn.neighbors import BallTree


def build_balltree(G):
    node_coords = np.array([(data['x'], data['y']) for n, data in G.nodes(data=True)])
    node_ids = [n for n, data in G.nodes(data=True)]
    return BallTree(node_coords), node_ids


def snap_with_balltree(gdf, balltree, node_ids):
    points_array = np.array([[geom.x, geom.y] for geom in gdf.geometry])
    _, indices = balltree.query(points_array, k=1)
    gdf['node_id'] = [node_ids[i[0]] for i in indices]
    return gdf
