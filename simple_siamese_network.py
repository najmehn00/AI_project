from signature.models.model import KerasBaseModel

from keras.layers import (
    Input,
    Lambda,
    MaxPooling2D,
    Dense,
    Flatten,
    Activation,
    Convolution2D,
)
from keras.models import Sequential, Model
from keras import backend as K


class simple_Siamese(KerasBaseModel):
    """simple_Siamese is based on Siamese Network,for detecting forgery signature"""

    def __init__(self, input_shape, dropout_rate=None, weight_decay_rate=None):
        """_summary_

        Args:
            input_shape (_type_): _description_
            dropout_rate (_type_, optional): _description_. Defaults to None.
            weight_decay_rate (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(input_shape, dropout_rate, weight_decay_rate)

    def initialize_base_network(self, input_shape):
        """_summary_

        Args:
            input_shape (_type_): _description_

        Returns:
            _type_: _description_
        """
        clf = Sequential()
        clf.add(Convolution2D(64, (3, 3), input_shape=input_shape))
        clf.add(Activation("relu"))
        clf.add(MaxPooling2D(pool_size=(2, 2)))
        clf.add(Convolution2D(32, (3, 3)))
        clf.add(Activation("relu"))
        clf.add(MaxPooling2D(pool_size=(2, 2)))
        clf.add(Flatten())
        clf.add(Dense(128, activation="relu"))
        clf.add(Dense(64, activation="relu"))
        return clf

    def euclidean_distance(self, vects):
        """_summary_

        Args:
            vects (_type_): _description_

        Returns:
            _type_: _description_
        """
        x, y = vects
        return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))

    def eucl_dist_output_shape(self, shapes):
        """_summary_

        Args:
            shapes (_type_): _description_

        Returns:
            _type_: _description_
        """
        shape1, shape2 = shapes
        return (shape1[0], 1)

    def build(self, input_shape, dropout_rate, weight_decay_rate):
        """_summary_

        Args:
            input_shape (_type_): _description_
            dropout_rate (_type_): _description_
            weight_decay_rate (_type_): _description_

        Returns:
            _type_: _description_
        """

        base_network = self.initialize_base_network(input_shape)
        img_a = Input(shape=input_shape)
        img_b = Input(shape=input_shape)
        vec_a = base_network(img_a)
        vec_b = base_network(img_b)
        distance = Lambda(
            self.euclidean_distance, output_shape=self.eucl_dist_output_shape
        )([vec_a, vec_b])
        prediction = Dense(2, activation="softmax")(distance)
        model = Model([img_a, img_b], prediction)

        return model
