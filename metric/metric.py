import numpy as np

from data_structure.data_structure import StaticData


def calculate_tf_idf(tf, df, doc_num):
    """

    :param doc_num: the number of all documents
    :param tf: term frequency
    :param df: document frequency where term appears
    :return: td-idf importance
    """
    idf = np.log(float(doc_num + 1) / (df + 1))
    tf = 1.0 + np.log(tf)
    return tf * idf


def calculate_static_data(documents):
    """Calculate static data

    :return:
    """
    df_term_class = {}
    tf_term_class = {}
    for document in documents:
        for term, tf in document.tfs['all'].items():
            if term not in df_term_class:
                df_term_class[term] = {}
            if term not in tf_term_class:
                tf_term_class[term] = {}
            for class_ in document.class_['topics']:
                add_value(df_term_class[term], class_, 1)
                add_value(tf_term_class[term], class_, tf)
    StaticData.df_term_class = df_term_class
    StaticData.tf_term_class = tf_term_class


def calculate_chi_2():
    """Calculate chi square metric to measure the importance of a term to a class.

    :return:
    """
    chi_2_term_class = {}

    for term in StaticData.df_term.keys():
        if term not in StaticData.df_term_class:
            StaticData.df_term_class[term] = {}
        if term not in StaticData.tf_term_class:
            StaticData.tf_term_class[term] = {}
        if term not in chi_2_term_class:
            chi_2_term_class[term] = {}
        for class_ in StaticData.bag_of_classes:
            if class_ not in StaticData.df_term_class[term]:
                StaticData.df_term_class[term][class_] = 0.0
            if class_ not in StaticData.tf_term_class[term]:
                StaticData.tf_term_class[term][class_] = 0.0

            A = StaticData.df_term_class[term][class_]

            if A != 0:
                B = StaticData.df_term[term] - A
                C = StaticData.df_of_classes[class_] - A
                D = StaticData.n_train_documents - A - B - C
                N = A + B + C + D

                chi_2_term_class[term][class_] = (float(N) * (A * D - C * B) * (A * D - C * B)) \
                                                 / ((A + C) * (B + D) * (A + B) * (C + D))
            else:
                chi_2_term_class[term][class_] = 0.0

    StaticData.chi_2_term_class = chi_2_term_class
    return StaticData.chi_2_term_class


def calculate_tf_class():
    """

    :return:
    """

    for term in StaticData.df_term.keys():
        if term not in StaticData.tf_avg_term_class:
            StaticData.tf_avg_term_class[term] = {}
        for class_ in StaticData.bag_of_classes:
            StaticData.tf_avg_term_class[term][class_] = float(StaticData.tf_term_class[term][class_]) \
                                                         / StaticData.df_of_classes[class_]

    return StaticData.tf_avg_term_class


def calculate_term_entropy_in_class(raw_documents):
    """

    :return:
    """

    class_has_documents = {}
    entropy_term_class = {}
    for document in raw_documents:
        for class_ in document.class_['topics']:
            if class_ not in class_has_documents:
                class_has_documents[class_] = []
            class_has_documents[class_].append(document)

    StaticData.class_has_documents = class_has_documents

    for class_ in StaticData.bag_of_classes:
        for document in class_has_documents[class_]:
            for term in document.tfs['all'].keys():
                if term not in entropy_term_class:
                    entropy_term_class[term] = {}
                p = float(document.tfs['all'][term]) / StaticData.tf_term_class[term][class_]
                entropy_term_class[term][class_] = entropy_term_class[term].setdefault(class_, 0.0) - p * np.log(p)

    StaticData.entropy_term_class = entropy_term_class
    return StaticData.entropy_term_class


def calculate_beta_factor():
    """

    :return:
    """

    beta = {}
    for term in StaticData.df_term.keys():
        beta[term] = {}
        for class_ in StaticData.bag_of_classes:
            beta[term][class_] = StaticData.df_term_class[term][class_] \
                                 - float(StaticData.df_term[term]) / StaticData.n_classes

    StaticData.beta = beta
    return beta


def calculate_ichi_metric(raw_documents):
    """Calculate ichi importance for sorting terms to limit the cardinality of feature vector.

    :return:
    """

    print("Calculate the chi square metric: chi_2_term_class[term][class]...")
    chi_2_term_class = calculate_chi_2()
    print("Calculate normalized term frequency of terms vs classes: tf_class[term][class]...")
    tf_class = calculate_tf_class()
    print("Calculate information entropy of terms vs classes: entropy_term_class[term][class]...")
    entropy_term_class = calculate_term_entropy_in_class(raw_documents)
    print("Calculate modified factor β for chi square metric...")
    beta = calculate_beta_factor()
    ichi = {}
    ichi_term_class = {}
    print("Combine them to calculate my importance metric ichi for each term...")
    for term in StaticData.df_term.keys():
        ichi[term] = 0.0
        ichi_term_class[term] = {}
        for class_ in StaticData.bag_of_classes:
            ichi_term_class[term][class_] = chi_2_term_class[term][class_] \
                                            * tf_class[term][class_] \
                                            * entropy_term_class.setdefault(term, {}).setdefault(class_, 0.0) \
                                            * beta[term][class_]
            ichi[term] = max(ichi[term], ichi_term_class[term][class_])

    StaticData.ichi = ichi
    StaticData.ichi_term_class = ichi_term_class
    return ichi


def add_value(dict_, key, value):
    if key not in dict_:
        dict_[key] = 0
    dict_[key] += value


def find(x, f):
    if (x != f[x]):
        f[x] = find(f[x], f)
    return f[x]


def max_label(index, labels):
    freq = {}
    f = {}

    for i in index:
        f[i] = i

    for i in index:
        for j in index:
            root1 = find(i, f)
            root2 = find(j, f)
            if root1 != root2:
                if len(labels[i].intersection(labels[j])) > 0:
                    f[root1] = root2

    label_ = ''
    e = 0.0

    for i in index:
        print("label: {}, f[i]: {}, i: {}".format(labels[i], f[i], i))
        if f[i] not in freq.keys():
            freq[f[i]] = 0
        freq[f[i]] += 1
        if e < freq[f[i]]:
            e = freq[f[i]]
            label_ = labels[f[i]]

    print("e: {}, label: {}".format(e, label_))
    print(len(index))
    return label_, float(e) / len(index)


def calculate_purity(centroids_, cluster_assign_, labels, k):
    purity = 0.0
    m = cluster_assign_.shape[0]

    for i in range(k):
        in_class_dataSet = np.where(cluster_assign_[:, 0] == i)[0]
        label_, p = max_label(in_class_dataSet, labels)
        print(p)
        print("{} / {} = {}".format(float(len(in_class_dataSet)), m, float(len(in_class_dataSet)) / m))
        purity += p * float(len(in_class_dataSet)) / m
        print("purity: {}".format(purity))

    return purity


def euclidean(x_, y_):
    return np.linalg.norm(x_ - y_)