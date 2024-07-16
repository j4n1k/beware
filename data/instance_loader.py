class InstanceLoader:
    def __init__(self):
        self.general_info = None
        self.articles = None
        self.skus = None
        self.orders = None

    @staticmethod
    def read_data(path="data/instances/test"):
        file = open(path, "r")
        content = file.read()
        return content

    def extract_info(self):
        content = self.read_data()
        sections = content.split("SECTION")

        # Extracting and processing each section
        header = sections[0]
        article_data = sections[1].split("\n")[1:-1]
        sku_data = sections[2].split("\n")[1:-1]
        order_data = sections[3].split("\n")[1:-1]

        # Parsing header information
        header_info = {}
        for line in header.split("\n"):
            if line:
                if " : " in line:
                    key, value = line.split(" : ")
                    header_info[key.strip()] = value.strip()

        # Creating article dictionary
        articles = {}
        for line in article_data:
            parts = line.split()
            if " : " not in line:
                articles[int(parts[1])] = {"weight": int(parts[3])}

        # Creating SKU dictionary
        skus = {}
        for line in sku_data:
            parts = line.split()
            if not " : " in line:
                skus[int(parts[1])] = {
                    "aisle": int(parts[3]),
                    "cell": int(parts[5]),
                    "quantity": int(parts[7]),
                    "side": parts[9]
                }

        # Creating orders list
        orders = []
        current_order = []
        for line in order_data:
            line = line.strip()
            if line.startswith("NUM_ARTICLES_IN_ORDER"):
                # If there's a current order being processed, add it to orders
                if current_order:
                    orders.append(current_order)
                    current_order = []
            elif line.startswith("ID"):
                parts = line.split()
                product_id = int(parts[1])
                quantity = int(parts[3])
                current_order.append([product_id, quantity])

        if current_order:
            orders.append(current_order)

        self.general_info = header_info
        self.skus = skus
        self.orders = orders
        self.articles = articles

    def create_graph(self):
        pass

    def print_instance(self):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("Header Info:")
        pp.pprint(self.general_info)
        print("\nArticles:")
        pp.pprint(self.articles)
        print("\nSKUs:")
        pp.pprint(self.skus)
        print("\nOrders:")
        pp.pprint(self.orders)
