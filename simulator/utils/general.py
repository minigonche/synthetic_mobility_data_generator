


def binary_search(search_val, array):
    '''
    Method that searches in the given array in a binary fashion

    Parameters
    ----------
    search_val : object
        The value to search

    array : list
        List for searching

    Return
    ------
    int
        The position of the closest value less or equal to the given value. Returns -1 if the list is empty.
    '''

    if len(array) == 0:
        return -1

    low = 0
    high = len(array) - 1
    closest_index = -1

    while low <= high:
        mid = (low + high) // 2
        if array[mid] <= search_val:
            closest_index = mid
            low = mid + 1
        else:
            high = mid - 1

    return closest_index