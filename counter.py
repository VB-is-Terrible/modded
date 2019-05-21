import re, math, sys, os

TEMP_FILE = 'temp.order'

templates = {}

class Ingredient:
    def __init__(self):
        self.name = ''
        self.count = 1
    def setContent(self, line):
        pattern = r'(\d+)\s*(.*)'
        match = re.match(pattern, line)
        count = int(match.group(1))
        item = match.group(2)

        self.name = item.strip()
        self.count = count

    def __repr__(self):
        return '{}\t{}'.format(self.count, self.name)


class Order:
    def __init__(self):
        self.ingredients = []
        self.name = ''
        self.count = 1
        self.template = False

    def setHeading(self, heading):
        if heading.startswith('#'):
            self.template = True
            heading = heading[1:]

        pattern = r'^([^\(]*)(\(.*)?$'
        match = re.match(pattern, heading)
        self.name = match.group(1).strip()
        self.count = self.getCount(match.group(2))
        if not self.template:
            self.count = math.ceil(self.count)

    def __repr__(self):
        result = '{} (x{})\n'.format(self.name, self.count)
        for ingredient in self.ingredients:
            result += str(ingredient) + '\n'
        return result


    @staticmethod
    def getCount(parens):
        if parens == None or '(' not in parens:
            return 1

        parenPattern = r'\s*\((.*?)\)(.*)'
        match = re.match(parenPattern, parens)
        equate = match.group(1)
        nextParen = match.group(2)

        num = int(equate[1:])
        if equate[0] == 'x':
            mul = num
        elif equate[0] == '/':
            mul = 1/num
        else:
            raise Exception('Invalid operator: {}'.format(equate[0]))

        return mul * Order.getCount(nextParen)

class Parser:
    def __init__(self, descent = 0):
        self.orders = []
        self.currentLine = ''
        self.file = None
        self.descent = descent
        self.next = None
    
    def _validLine(self):
        if self.currentLine != '' and self.currentLine.strip() == '':
            return False
        elif self.currentLine.startswith('//'):
            return False
        else:
            return True

    def _accept(self):
        self.currentLine = self.file.readline()

    def readLine(self):
        self._accept()
        while True:
            while not self._validLine():
                self._accept()
            if self.currentLine.startswith('/*'):
                while self.currentLine != '' and not self.currentLine.startswith('*/'):
                    self._accept()
                if self.currentLine.startswith('*/'):
                    self._accept()
                continue
            else:
                self.currentLine = self.currentLine.strip()
                return


    def parse(self, file):
        self.file = file
        self.readLine()
        while self.currentLine != '':
            order = self._parseOrder()
            if order.template:
                if order.name in templates:
                    raise Exception('Duplicate template: {}'.format(order.name))
                templates[order.name] = order
            else:
                self.orders.append(order)
        sortFunc = lambda x: x.name
        self.orders.sort(key = sortFunc)
        self.recurse()

    def _parseOrder(self):
        order = Order()
        order.setHeading(self.currentLine)
        self.readLine()
        while self.currentLine != '' and self.currentLine[0].isnumeric():
            ingredient = self._parseIngredient()
            order.ingredients.append(ingredient)
        if len(order.ingredients) == 0:
            if order.name in templates:
                order.ingredients = templates[order.name].ingredients
            else:
                raise Exception('Empty order')
        return order

    def _parseIngredient(self):
        ingredient = Ingredient()
        ingredient.setContent(self.currentLine)
        self.readLine()
        return ingredient

    def total(self):
        total = {}
        for order in self.orders:
            for ingredient in order.ingredients:
                add = ingredient.count * order.count
                if ingredient.name in total:
                    total[ingredient.name] += add
                else:
                    total[ingredient.name] = add
        return total

    def list_ingredients(self):
        total = self.total()
        l = sorted(total.keys())
        result = ''
        for i in l:
            result += '{1}\t{0}'.format(i, total[i]) + '\n'
        return result

    def list_orders(self):
        result = ''
        for order in self.orders:
            result += '{}\t(x{})\n\n'.format(order.name, order.count)
            for ingredient in order.ingredients:
                result += '{}\t{}\n'.format(ingredient.count * order.count, ingredient.name)
            result += '\n'
        return result

    def recurse(self):
        total = self.total()
        carry_over = []
        repeat = []
        for item in total.keys():
            if item in templates:
                repeat.append(item)
            else:
                carry_over.append(item)
        if len(repeat) != 0:
            carry_over.sort()
            repeat.sort()
            parser = self.create(repeat, carry_over, total)
        else:
            parser = None
        self.next = parser
        if parser is not None:
            parser.recurse()
        return parser

    def create(self, repeat, carry_over, total):
        
        parser = Parser(self.descent + 1)
        for item in repeat:
            order = Order()
            order.name = item
            order.count = math.ceil(total[item] * templates[item].count)
            order.ingredients = templates[item].ingredients
            parser.orders.append(order)
        carry_order = Order()
        carry_order.name = 'Carry Over'
        for item in carry_over:
            ingredient = Ingredient()
            ingredient.name = item
            ingredient.count = total[item]
            carry_order.ingredients.append(ingredient)
        if len(carry_order.ingredients) != 0:    
            parser.orders.append(carry_order)
        return parser
            
    def pprint(self):
        result = ''
        result += makeHeading('DESCENT {}'.format(self.descent))
        result += makeHeading('ORDERS') + '\n'
        result += self.list_orders() + '\n'
        result += makeHeading('MATERIALS') + '\n'
        result += self.list_ingredients() + '\n'
        result += '\n'
        if self.next is not None:
            result += self.next.pprint()
        return result
        


def loadTemplates():
    templates = os.listdir('templates')
    for templateFile in templates:
        if os.path.isfile(os.path.join('templates', templateFile)):
            fin = open(os.path.join('templates', templateFile))
            parser = Parser()
            parser.parse(fin)
            fin.close()

def test():
    go('ie_total2.txt')

def go(filename):
    a = open(filename)
    global parser
    parser = Parser()
    parser.parse(a)
    a.close()
    print(parser.pprint())
    

def makeHeading(string):
    LENGTH = 50
    PADDING = '-'
    message = ' {} '.format(string)
    left_over = LENGTH - len(message)
    right = left_over // 2
    left = left_over - right
    return PADDING * left + message + PADDING * right + '\n'

def inputOrder():
    output = open(TEMP_FILE, 'w')
    print("Input order:")
    line = input()
    empty = False
    while not empty and line != '':
        if line == '':
            empty = True
        output.write(line)
        line = input()
    output.close()
    print('Working')

def main():
    if len(sys.argv) == 1:
        inputOrder()
        file = TEMP_FILE
    elif len(sys.argv) != 2:
        raise Exception('Invalid number of arguements')
    else:
        file = sys.argv[1]
    
    loadTemplates()
    with open(file) as fin:
        parser = Parser()
        parser.parse(fin)
        fin.close()
        print(parser.pprint())
        
if __name__ == '__main__':
    main()

