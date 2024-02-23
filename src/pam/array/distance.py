import numpy as np


def accuracy(actual: np.array, predicted: np.array) -> float:
    assert actual.shape == predicted.shape
    correct = 0
    for ia, ib in zip(actual, predicted):
        if np.argmax(ia) == np.argmax(ib):
            correct += 1
    return correct / len(predicted)


def cross_entropy(actual: np.array, predicted: np.array) -> float:
    assert actual.shape == predicted.shape
    epsilon = 1e-12
    predicted = np.clip(predicted, epsilon, 1.0 - epsilon)
    return -np.sum(actual * np.log(predicted)) / actual.shape[0]
