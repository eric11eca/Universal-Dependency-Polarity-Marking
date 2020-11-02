import numpy as np
from tqdm import tqdm
from copy import deepcopy
from binarization import Binarizer
from dependency_parse import dependencyParse, stanzaParse
from util import det_type, det_mark, negtive_implicative
from util import heapq, arrows, negate_mark, btreeToList, convert2vector


class Polarizer:
    def __init__(self, dependtree=None, relation=None):
        self.dependtree = dependtree
        self.sentence_head = []
        self.relation = relation
        self.polarize_function = {
            "acl:relcl": self.polarize_acl_relcl,
            "acl": self.polarize_acl_relcl,
            "advcl": self.polarize_acl_relcl,
            "nsubj": self.polarize_nsubj,
            "nsubj:pass": self.polarize_nsubj,
            "dep": self.polarize_dep,
            "det": self.polarize_det,
            "obj": self.polarize_obj,
            "case": self.polarize_case,
            "obl": self.polarize_obl,
            "amod": self.polarize_amod,
            "conj": self.polarize_inherite,
            "cc": self.polarize_cc,
            "advmod": self.polarize_advmod,
            "aux": self.polarize_inherite,
            "aux:pass": self.polarize_inherite,
            "obl:npmod": self.polarize_oblnpmod,
            "nummod": self.polarize_nummod,
            "cop": self.polarize_inherite,
            "xcomp": self.polarize_obj,
            "mark": self.polarize_inherite,
            "expl": self.polarize_inherite,
            "nmod": self.polarize_nmod,
            "compound": self.polarize_inherite,
            "compound:prt": self.polarize_inherite,
            "ccomp": self.polarize_ccomp,
            "nmod:poss": self.polarize_nsubj,
            "fixed": self.polarize_inherite
        }
        self.treeLog = []
        self.polarLog = []

    def polarize_deptree(self):
        self.polarize(self.dependtree)

    def polarize(self, tree):
        if tree.isTree():
            self.polarize_function[tree.val](tree)

    def polarize_acl_relcl(self, tree):
        self.polarLog.append("polarize_acl:relcl")
        right = tree.getRight()
        left = tree.getLeft()

        if right.isTree():
            self.polarize(right)
        else:
            right.mark = "+"

        tree.mark = right.mark
        if left.isTree():
            self.polarize(left)

        if right.mark == "-":
            self.negate(left, -1)
        elif right.mark == "=":
            self.equalize(left)

    def polarize_nsubj(self, tree):
        self.polarLog.append("polarize_nsubj")
        self.sentence_head.append(tree)
        right = tree.getRight()
        left = tree.getLeft()

        if tree.mark != "0":
            right.mark = tree.mark
            left.mark = tree.mark
        else:
            right.mark = '+'
            left.mark = '+'

        self.polarize(right)
        if left.val.lower() == "that":
            self.equalize(right)

        if left.isTree():
            self.polarize(left)
        else:
            if left.val.lower() in ["nobody"]:
                self.negate(tree, self.relation.index(tree.key))

        if tree.mark == "0":
            tree.mark = right.mark
        self.sentence_head.pop()

    def polarize_dep(self, tree):
        self.polarLog.append("polarize_dep")

        right = tree.getRight()
        left = tree.getLeft()

        left.mark = "+"
        right.mark = "+"

        if right.isTree():
            self.polarize(right)

        if left.isTree():
            self.polarize(left)

    def polarize_obj(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        if tree.mark != "0":
            right.mark = tree.mark
            left.mark = tree.mark
        else:
            right.mark = '+'
            left.mark = '+'

        if self.sentence_head[-1].left.npos == "PRP":
            right.mark = "="

        if right.isTree():
            self.polarize(right)

        if left.isTree():
            self.polarize(left)

        if right.val.lower() in negtive_implicative:
            self.negate(left, -1)

        tree.mark = left.mark

    def polarize_obl(self, tree):
        self.polarLog.append("polarize_obl")

        right = tree.getRight()
        left = tree.getLeft()

        left.mark = tree.mark
        if left.isTree():
            self.polarize(left)
        else:
            left.mark = '+'

        right.mark = tree.mark
        if right.isTree():
            self.polarize(right)
        else:
            right.mark = '+'

    def polarize_det(self, tree):
        self.polarLog.append("polarize_det")
        if not isinstance(tree.parent.parent, str) and not isinstance(tree.parent, str):
            isNmod = tree.parent.parent.val == "nmod"
            isCase = tree.parent.val == "case"
            isDet = tree.parent.parent.right.val == "det"
            isEqual = tree.mark == "="
            if isNmod and isCase and isDet and isEqual:
                self.polarize_inherite(tree)
                return

        right = tree.getRight()
        left = tree.getLeft()

        detType = det_type(left.val)
        detMark = det_mark[detType]

        if tree.mark != "0" and len(self.sentence_head) > 1:
            left.mark = tree.mark
        else:
            left.mark = detMark[0]

        right.mark = detMark[1]
        tree.mark = detMark[1]

        if right.isTree():
            self.polarize(right)

        if detType == "det:negation":
            self.negate(self.sentence_head[-1], self.relation.index(tree.key))

    def polarize_inherite(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        right.mark = tree.mark
        if right.isTree():
            self.polarize(right)

        left.mark = tree.mark
        if left.isTree():
            self.polarize(left)

    def polarize_cc(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        left.mark = '+'
        if right.isTree():
            self.polarize(right)
        else:
            right.mark = tree.mark

    def polarize_nmod_poss(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        left.mark = tree.mark
        if left.isTree():
            self.polarize(left)
        else:
            left.mark = '+'

        right.mark = tree.mark
        if right.isTree():
            self.polarize(right)
        else:
            left.mark = '+'

    def polarize_amod(self, tree):
        left = tree.getLeft()
        right = tree.getRight()
        if left.val.lower() in ["many", "most"]:
            left.mark = "+"
            right.mark = "="
            if right.isTree():
                self.polarize(right)
        else:
            self.polarize_inherite(tree)

    def polarize_advmod(self, tree):
        left = tree.getLeft()
        right = tree.getRight()

        if left.val.lower() in ["many", "most"]:
            left.mark = "+"
            right.mark = "="
            if right.isTree():
                self.polarize(right)
        elif left.val.lower() in ["not", "no", "n’t"]:
            left.mark = "+"
            right.mark = tree.mark
            if right.isTree():
                self.polarize(right)
            self.negate(tree, self.relation.index(left.key))
        else:
            self.polarize_inherite(tree)

    def polarize_case(self, tree):
        self.polarLog.append("polarize_case")

        right = tree.getRight()
        left = tree.getLeft()

        if tree.mark != "0":
            left.mark = tree.mark
            right.mark = tree.mark
        else:
            left.mark = "+"
            right.mark = "+"
        if right.val == "least":
            tree.mark = "-"
            right.mark = "+"
            left.mark = right.mark
        elif right.val == "most":
            tree.mark = "+"
            right.mark = "+"
            left.mark = right.mark
            self.negate(self.sentence_head[-1], self.relation.index(tree.key))
        # elif left.val == "in":
        #    right.mark = "-"
        elif right.npos == "CD":
            right.mark = "="
            if left.isTree():
                self.polarize(left)
        elif right.val == "nmod:poss":
            left.mark = "="
            if right.isTree():
                self.polarize(right)
        else:
            if right.isTree():
                self.polarize(right)
            if left.isTree():
                self.polarize(left)

    def polarize_oblnpmod(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        if left.isTree():
            self.polarize(left)
        right.mark = left.mark
        if right.isTree():
            self.polarize(right)

    def polarize_nummod(self, tree):
        self.polarLog.append("polarize_nummod")
        right = tree.getRight()
        left = tree.getLeft()

        left.mark = "-"
        right.mark = "+"

        if left.val.lower() in ["one", "1"]:
            left.mark = "="

        if tree.parent == "compound":
            right.mark = left.mark

        if right.isTree():
            self.polarize(right)

        if left.isTree():
            self.polarize(left)
        elif left.id == 1:
            left.mark = "="

    def polarize_nmod(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        if right.isTree():
            self.polarize(right)

        left.mark = right.mark
        if left.isTree():
            self.polarize(left)

        tree.mark = right.mark

    def polarize_ccomp(self, tree):
        right = tree.getRight()
        left = tree.getLeft()

        if tree.mark != "0":
            right.mark = tree.mark

        if right.isTree():
            self.polarize(right)

        left.mark = right.mark
        if left.isTree():
            self.polarize(left)

        # tree.mark = right.mark

    def equalize(self, tree):
        if tree.isTree():
            if tree.val != "nummod":
                self.equalize(tree.getRight())
                self.equalize(tree.getLeft())
                if tree.mark != "0":
                    tree.mark = "="
        else:
            if tree.npos != "CC":
                tree.mark = "="

    def negate_condition(self, tree, anchor):
        not_truch_connection = not tree.val in ["and", "or"]
        not_empty_mark = tree.mark != "0"
        return not_empty_mark and not_truch_connection

    def negate(self, tree, anchor):
        if tree.isTree():
            # print(tree.val)
            if self.relation.index(tree.key) > anchor or "nsubj" in tree.val:
                # print(tree.val)
                self.negate(tree.getRight(), anchor)
                self.negate(tree.getLeft(), anchor)
                if self.negate_condition(tree, anchor):
                    tree.mark = negate_mark[tree.mark]
        else:
            if self.relation.index(tree.key) > anchor and self.negate_condition(tree, anchor):
                if tree.npos != "EX":
                    tree.mark = negate_mark[tree.mark]


def run_polarize_pipeline(sentences, annotations_val=[], verbose=0):
    binarizer = Binarizer()
    polarizer = Polarizer()

    annotations = []
    incorrect = []
    exceptioned = []

    for i in tqdm(range(len(sentences))):
        # Universal Dependency Parse
        sent = sentences[i]
        tree, postag, words = stanzaParse(sent)
        parseTreeCopy = deepcopy(tree)

        # Binarization
        binarizer.parseTable = parseTreeCopy
        binarizer.postag = postag
        binarizer.words = words
        sexpression = ""
        annotated = ""

        try:
            binaryDepdency, relation = binarizer.binarization()
            if verbose == 2:
                sexpression, annotated = btreeToList(
                    binaryDepdency, len(words), 0)
                sexpression = str(sexpression).replace(
                    ',', ' ').replace("'", '')
        except Exception as e:
            if verbose == 2:
                print(str(e))
            exceptioned.append((sent, annotations_val[i]))
            continue

        # Polarization
        polarizer.dependtree = binaryDepdency
        polarizer.relation = relation
        try:
            polarizer.polarize_deptree()
        except Exception as e:
            if verbose == 2:
                print(str(e))
            exceptioned.append((sent, annotations_val[i]))
            continue

        # Postprocessing
        polarized, annotated = btreeToList(binaryDepdency, len(words), 0)
        polarized = str(polarized).replace(',', ' ').replace("'", '')

        result = []
        while annotated:
            next_item = heapq.heappop(annotated)
            result.append(next_item[1])

        result = str(result).replace(',', ' ').replace(
            "'", '').replace("[", "").replace("]", "")

        vec = convert2vector(result)
        if len(annotations_val) > 0:
            annotation_val = annotations_val[i]
            vec_val = convert2vector(annotation_val)
            if len(vec) == len(vec_val):
                if np.prod(vec_val) != -1:
                    if np.sum(np.subtract(vec, vec_val)) != 0:
                        one = not "1" in annotation_val
                        two = not "2" in annotation_val
                        three = not "3" in annotation_val
                        four = not "4" in annotation_val
                        five = not "5" in annotation_val
                        if one and two and three and four and five:
                            incorrect.append((sent, annotation_val))
                            continue

        # if verbose == 3:
        # print(polarizer.polarLog)

        annotations.append({
            "annotated": result,
            "polarized": polarized,
            "sexpression": sexpression,
        })

    return annotations, exceptioned, incorrect