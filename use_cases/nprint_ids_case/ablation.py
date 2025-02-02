import os
import csv
import graphviz
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

from sklearn import tree
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import train_test_split

from trustee.utils import log
from trustee import ClassificationTrustee

from autogluon.tabular import TabularPredictor
from nprintml.label.aggregator import registry as aggregators

AGGREGATOR = "pcap"
LABELS_PATH = "res/nprint_dataset/sub_labels.txt"
# LABELS_PATH = "res/nprint_dataset/labels.txt"
MODELS_PATH = "res/nprint_dataset/nprintml/model"
# NPRINT_PATH = "res/nprint_dataset/nprintml/nprint"
NPRINT_PATH = "res/nprint_dataset/nprintml/sub_nprint"
OUTPUT_PATH = "res/output/full_model/"


def main():
    logger = log.Logger("{}/output.log".format(OUTPUT_PATH))
    logger.log("Reading nPrint dataset...")

    aggr = aggregators[AGGREGATOR](LABELS_PATH)
    df = aggr(NPRINT_PATH)

    y = df["label"]
    X = df.drop(labels=["label"], axis=1)

    X_indexes = np.arange(0, X.shape[0])
    X_train, X_test, y_train, y_test = train_test_split(X_indexes, y, train_size=0.7)
    X_train = X.iloc[X_train]
    X_test = X.iloc[X_test]
    logger.log("X size: {}; y size: {}".format(len(X), len(y)))
    logger.log("Done!")

    logger.log("Loading nPrintML model...")
    blackbox = TabularPredictor.load(MODELS_PATH, verbosity=1)
    logger.log("Done!")

    y_pred = blackbox.predict(X_test)
    logger.log("Blackbox model classification report with IID:")
    logger.log("\n{}".format(classification_report(y_test, y_pred, digits=3)))

    output_dir = f"{OUTPUT_PATH}/ablation"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    num_iter = 10
    train_size = 0.7
    with open(f"{output_dir}/ablation.csv", "w") as f:
        # create the csv writer
        writer = csv.writer(f)
        writer.writerow(
            [
                "iteration",
                "samples size",
                "method",
                "dt_size",
                "fidelity_macro",
                "accuracy_macro",
                "fidelity_weighted",
                "accuracy_weighted",
            ]
        )

        for samples_size in np.arange(0.05, 0.55, 0.1):
            for i in range(10):
                #####################################
                ############# STRAWMAN ##############
                #####################################

                size = int(int(len(X_train)) * samples_size)
                samples_idxs = np.random.choice(len(X_train), size=size, replace=False)
                X_iter, y_iter = X_train.iloc[samples_idxs], y_train.iloc[samples_idxs]

                X_sample_train, _, _, _ = train_test_split(X_iter, y_iter, train_size=train_size)
                y_pred_train = blackbox.predict(X_sample_train)

                dt = tree.DecisionTreeClassifier()
                dt = dt.fit(X_sample_train, y_pred_train)
                dt_y_pred = dt.predict(X_test)

                logger.log("Straw-man explanation global fidelity report:")
                logger.log("\n{}".format(classification_report(y_pred, dt_y_pred, digits=3)))

                logger.log("Straw-man explanation classification report:")
                logger.log("\n{}".format(classification_report(y_test, dt_y_pred, digits=3)))

                writer.writerow(
                    [
                        i,
                        samples_size,
                        "ablation",
                        dt.tree_.node_count,
                        f1_score(y_pred, dt_y_pred, average="macro"),
                        f1_score(y_test, dt_y_pred, average="macro"),
                        f1_score(y_pred, dt_y_pred, average="weighted"),
                        f1_score(y_test, dt_y_pred, average="weighted"),
                    ]
                )

                #######################################
                ######### NOtrustee + ACCURACY #########
                #######################################

                logger.log("Using Classification Trustee algorithm to extract DT...")
                trustee = ClassificationTrustee(expert=blackbox)

                trustee.fit(
                    X_train,
                    y_train,
                    num_iter=num_iter,
                    train_size=train_size,
                    samples_size=samples_size,
                    optimization="accuracy",
                    aggregate=False,
                    verbose=True,
                )

                logger.log("#" * 10, "Explanation validation", "#" * 10)
                (dt, reward, idx) = trustee.explain()

                logger.log("Accuracy-based  model explanation {} local fidelity: {}".format(idx, reward))
                dt_y_pred = dt.predict(X_test)

                logger.log("Accuracy-based model explanation w/o dataset aggregation global fidelity report:")
                logger.log("\n{}".format(classification_report(y_pred, dt_y_pred, digits=3)))

                logger.log("Accuracy-based model explanation w/o dataset aggregation classification report:")
                logger.log("\n{}".format(classification_report(y_test, dt_y_pred, digits=3)))

                writer.writerow(
                    [
                        i,
                        samples_size,
                        "no_trustee_accuracy",
                        dt.tree_.node_count,
                        f1_score(y_pred, dt_y_pred, average="macro"),
                        f1_score(y_test, dt_y_pred, average="macro"),
                        f1_score(y_pred, dt_y_pred, average="weighted"),
                        f1_score(y_test, dt_y_pred, average="weighted"),
                    ]
                )

                #######################################
                ######### NOtrustee + FIDELITY #########
                #######################################

                logger.log("Using Classification Trustee algorithm to extract DT...")
                trustee = ClassificationTrustee(expert=blackbox)

                trustee.fit(
                    X_train,
                    y_train,
                    num_iter=num_iter,
                    train_size=train_size,
                    samples_size=samples_size,
                    optimization="accuracy",
                    aggregate=False,
                    verbose=True,
                )

                logger.log("#" * 10, "Explanation validation", "#" * 10)
                (dt, reward, idx) = trustee.explain()

                logger.log("Accuracy-based  model explanation {} local fidelity: {}".format(idx, reward))
                dt_y_pred = dt.predict(X_test)

                logger.log("Accuracy-based model explanation w/o dataset aggregation global fidelity report:")
                logger.log("\n{}".format(classification_report(y_pred, dt_y_pred, digits=3)))

                logger.log("Accuracy-based model explanation w/o dataset aggregation classification report:")
                logger.log("\n{}".format(classification_report(y_test, dt_y_pred, digits=3)))

                writer.writerow(
                    [
                        i,
                        samples_size,
                        "no_trustee_fidelity",
                        dt.tree_.node_count,
                        f1_score(y_pred, dt_y_pred, average="macro"),
                        f1_score(y_test, dt_y_pred, average="macro"),
                        f1_score(y_pred, dt_y_pred, average="weighted"),
                        f1_score(y_test, dt_y_pred, average="weighted"),
                    ]
                )

                #####################################
                ######### trustee + ACCURACY #########
                #####################################

                logger.log("Using Classification Trustee algorithm to extract DT...")
                trustee = ClassificationTrustee(expert=blackbox)

                trustee.fit(
                    X_train,
                    y_train,
                    num_iter=num_iter,
                    train_size=train_size,
                    samples_size=samples_size,
                    optimization="accuracy",
                    verbose=True,
                )

                logger.log("#" * 10, "Explanation validation", "#" * 10)
                (dt, reward, idx) = trustee.explain()

                logger.log("Accuracy-based  model explanation {} local fidelity: {}".format(idx, reward))
                dt_y_pred = dt.predict(X_test)

                logger.log("Accuracy-based model explanation global fidelity report:")
                logger.log("\n{}".format(classification_report(y_pred, dt_y_pred, digits=3)))

                logger.log("Accuracy-based  model explanation classification report:")
                logger.log("\n{}".format(classification_report(y_test, dt_y_pred, digits=3)))

                writer.writerow(
                    [
                        i,
                        samples_size,
                        "trustee_accuracy",
                        dt.tree_.node_count,
                        f1_score(y_pred, dt_y_pred, average="macro"),
                        f1_score(y_test, dt_y_pred, average="macro"),
                        f1_score(y_pred, dt_y_pred, average="weighted"),
                        f1_score(y_test, dt_y_pred, average="weighted"),
                    ]
                )

                #####################################
                ######### trustee + FIDELITY #########
                #####################################

                logger.log("Using Classification Trustee algorithm to extract DT...")
                trustee = ClassificationTrustee(expert=blackbox)

                trustee.fit(
                    X_train,
                    y_train,
                    num_iter=num_iter,
                    train_size=train_size,
                    samples_size=samples_size,
                    verbose=True,
                )

                logger.log("#" * 10, "Explanation validation", "#" * 10)
                (dt, reward, idx) = trustee.explain()

                logger.log("Fidelity-based model explanation {} local fidelity: {}".format(idx, reward))
                dt_y_pred = dt.predict(X_test)

                logger.log("Fidelity-based Model explanation global fidelity report:")
                logger.log("\n{}".format(classification_report(y_pred, dt_y_pred, digits=3)))

                logger.log("Fidelity-based model explanation classification report:")
                logger.log("\n{}".format(classification_report(y_test, dt_y_pred, digits=3)))

                writer.writerow(
                    [
                        i,
                        samples_size,
                        "trustee_fidelity",
                        dt.tree_.node_count,
                        f1_score(y_pred, dt_y_pred, average="macro"),
                        f1_score(y_test, dt_y_pred, average="macro"),
                        f1_score(y_pred, dt_y_pred, average="weighted"),
                        f1_score(y_test, dt_y_pred, average="weighted"),
                    ]
                )


def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return m, m - h, m + h


def plot_results():
    """Plots results of ablation approach comparison"""
    comparison = {
        "dt_size": {},
        "fidelity_macro": {},
        "accuracy_macro": {},
        "fidelity_weighted": {},
        "accuracy_weighted": {},
    }

    output_dir = f"{OUTPUT_PATH}/ablation"
    with open(f"{output_dir}/ablation.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)
        for line in reader:
            (
                _,
                samples_size,
                method,
                dt_size,
                fidelity_macro,
                accuracy_macro,
                fidelity_weighted,
                accuracy_weighted,
            ) = line
            samples_size = f"{float(samples_size):.2f}"

            if method not in comparison["dt_size"]:
                comparison["dt_size"][method] = {}
            if samples_size not in comparison["dt_size"][method]:
                comparison["dt_size"][method][samples_size] = []

            if method not in comparison["fidelity_macro"]:
                comparison["fidelity_macro"][method] = {}
            if samples_size not in comparison["fidelity_macro"][method]:
                comparison["fidelity_macro"][method][samples_size] = []

            if method not in comparison["fidelity_weighted"]:
                comparison["fidelity_weighted"][method] = {}
            if samples_size not in comparison["fidelity_weighted"][method]:
                comparison["fidelity_weighted"][method][samples_size] = []

            if method not in comparison["accuracy_macro"]:
                comparison["accuracy_macro"][method] = {}
            if samples_size not in comparison["accuracy_macro"][method]:
                comparison["accuracy_macro"][method][samples_size] = []

            if method not in comparison["accuracy_weighted"]:
                comparison["accuracy_weighted"][method] = {}
            if samples_size not in comparison["accuracy_weighted"][method]:
                comparison["accuracy_weighted"][method][samples_size] = []

            comparison["dt_size"][method][samples_size].append(int(dt_size))
            comparison["fidelity_macro"][method][samples_size].append(float(fidelity_macro))
            comparison["accuracy_macro"][method][samples_size].append(float(accuracy_macro))
            comparison["fidelity_weighted"][method][samples_size].append(float(fidelity_weighted))
            comparison["accuracy_weighted"][method][samples_size].append(float(accuracy_weighted))

    plots_dir = f"{OUTPUT_PATH}/ablation/plots"
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    for (metric, methods) in comparison.items():
        samples_sizes = list(methods.values())[0]
        x = list(samples_sizes.keys())

        labels = [method_name for (method_name, _) in methods.items()]
        y = [
            [mean_confidence_interval(samples) for samples in samples_sizes.values()]
            for (_, samples_sizes) in methods.items()
        ]

        plt.figure(figsize=(30, 3))  # width:20, height:3
        width = 0.2
        fig, ax = plt.subplots()
        locs = np.arange(len(x))  # the label locations
        num_col = len(x) or 1
        width = 0.95 / num_col
        colors = [
            "#d75d5b",
            "#a7c3cd",
            "#524a47",
            "#8a4444",
            "#c8c5c3",
            "#524a47",
            "#edeef0",
        ]

        for idx, values in enumerate(y):
            means = [val[0] for val in values]
            yerr = [val[2] - val[1] for val in values]
            delta_p = 0.125 + (width * idx)
            ax.bar(
                [p + delta_p for p in locs],
                means,
                width,
                yerr=yerr,
                label=labels[idx],
            )

        ax.set_xticks(locs)
        ax.set_xticklabels(x, rotation=60)
        plt.title(f"{metric}")
        plt.legend()
        fig.tight_layout()
        plt.savefig(f"{plots_dir}/plot_{metric}.pdf")
        plt.close()


if __name__ == "__main__":
    # main()
    plot_results()
