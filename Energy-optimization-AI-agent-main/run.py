from analytics.usage_analysis import UsageAnalyzer


def main():

    print("=" * 60)
    print("Energy Optimization Agent")
    print("=" * 60)

    analyzer = UsageAnalyzer()

    df = analyzer.load_processed_data()

    print()

    print(df.head())

    print()

    print(df.shape)


if __name__ == "__main__":
    main()