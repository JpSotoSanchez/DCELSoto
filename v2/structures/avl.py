class AVLNode:

    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.parent = None
        self.height = 1


class AVLTree:

    def __init__(self, key_function):
        self.root = None
        self.key_function = key_function
        self.node_map = {}

    def height(self, node):
        return node.height if node else 0

    def update_height(self, node):
        node.height = 1 + max(
            self.height(node.left),
            self.height(node.right)
        )

    def balance_factor(self, node):
        return self.height(node.left) - self.height(node.right)

    def rotate_left(self, x):
        y = x.right
        t2 = y.left

        y.left = x
        x.right = t2

        if t2:
            t2.parent = x

        y.parent = x.parent
        x.parent = y

        self.update_height(x)
        self.update_height(y)

        return y

    def rotate_right(self, y):
        x = y.left
        t2 = x.right

        x.right = y
        y.left = t2

        if t2:
            t2.parent = y

        x.parent = y.parent
        y.parent = x

        self.update_height(y)
        self.update_height(x)

        return x

    def rebalance(self, node):
        self.update_height(node)

        bf = self.balance_factor(node)

        if bf > 1:
            if self.balance_factor(node.left) < 0:
                node.left = self.rotate_left(node.left)

            return self.rotate_right(node)

        if bf < -1:
            if self.balance_factor(node.right) > 0:
                node.right = self.rotate_right(node.right)

            return self.rotate_left(node)

        return node