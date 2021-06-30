import numpy as np

from skexplain.utils import dataset, log, persist
from skexplain.utils.const import CIC_IDS_2017_DATASET_META

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

df_train_test_path = "res/dataset/CIC-IDS-2017/"
df_validate_path = "res/dataset/validation/heartbleed.csv"


def main():
    logger = log.Logger("res/output/output.log")

    logger.log("Reading CIC-IDS-2017 dataset...")
    # Step 1: Parse train-test def
    X, y, _, _, _ = dataset.read(
        df_train_test_path, metadata=CIC_IDS_2017_DATASET_META, as_df=True
    )
    logger.log("Done!")

    logger.log("Splitting dataset into training and test...")
    X_indexes = np.arange(0, X.shape[0])
    X_train, X_test, y_train, y_test = train_test_split(
        X_indexes, y, train_size=0.7, stratify=y
    )
    X_train = X.iloc[X_train]
    X_test = X.iloc[X_test]
    logger.log("Done!")

    # Step 2: Train black-box model with loaded dataset
    logger.log("#" * 10, "Model init", "#" * 10)
    model_path = "RandomForestClassifier_cic_ids_2017.joblib.zip"
    logger.log("Looking for pre-trained model: {}...".format(model_path))
    blackbox = persist.load_model(model_path)
    if not blackbox:
        logger.log("Training model: RandomForestClassifier...")
        blackbox = RandomForestClassifier(n_jobs=4)
        blackbox.fit(X_train, y_train)
        persist.save_model(blackbox, model_path)

    logger.log("Done!")

    y_pred = blackbox.predict(X_test)

    logger.log("Blackbox model classification report with IID:")
    logger.log(
        "\n{}".format(
            classification_report(
                y_test,
                y_pred,
                digits=3,
                target_names=CIC_IDS_2017_DATASET_META["classes"],
            )
        )
    )

    logger.log("Reading Heartbleed OOD dataset...")
    df_meta = CIC_IDS_2017_DATASET_META
    df_meta["is_dir"] = False
    X_validate, y_validate, _, _, _ = dataset.read(
        df_validate_path, metadata=df_meta, as_df=True
    )
    logger.log("Done!")

    y_val_pred = blackbox.predict(X_validate)

    logger.log("Blackbox model classification report with OOD:")
    logger.log(
        "\n{}".format(
            classification_report(
                y_validate,
                y_val_pred,
                digits=3,
                target_names=["BENIGN", "Heartbleed"],
            )
        )
    )


if __name__ == "__main__":
    main()
