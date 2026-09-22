# How Neural Networks Learn: From Rules to Weights

## The Problem with Hard-Coded Rules

Imagine you want to identify if an image is a dog or a cat using rules:

```go
if ears_are_pointy and whiskers_exist:
    return cat
```

**The problem:** Every image is different. You'd need different rules for every case.

## The Solution: Let the Model Learn

Instead of defining rules, we give the model inputs and let it learn the rules.

## A Neuron: The Basic Unit

A neuron is a small computation unit. It takes inputs, applies weights, and produces an output.

### Example: Dog vs Cat Classifier

```
Inputs:
  Weight = 4 kg
  Height = 30 cm
  Tail Length = 25 cm
```

Not all inputs are equally important. Height might matter more than tail length for classification.

So we assign **weights** (importance values) to each input:

```
score = 
  (Weight × A) +
  (Height × B) +
  (TailLength × C)
```

Where A, B, C are the weights. Higher weight = more influence.

### Concrete Example

```
score = 
  Weight × 10 +
  Height × 1 +
  TailLength × 0.5
```

Here:
- Weight has the highest importance (10)
- Height is moderate (1)
- Tail length is least important (0.5)

The neuron calculates a score. If score > threshold → Dog. Else → Cat.

## Training: How the Model Learns the Right Weights

The model starts with **completely random weights**. It makes wrong predictions.

Through training, it adjusts weights based on errors.

### The Guessing Analogy

Imagine guessing a number:

```
Guess = 100
Actual = 80

The guess is too high. Adjust down.
```

Neural networks do exactly this:

**If prediction is too high:**
- Decrease weight of inputs that pushed it too high

**If prediction is too low:**
- Increase weight of inputs that should influence more

### Example Training Process

```
Training data image 1:
- Prediction: Cat (wrong, it's actually a Dog)
- Adjust: Increase weight of Height, decrease weight of TailLength

Training data image 2:
- Prediction: Dog (correct!)
- No adjustment needed

Training data image 3:
- Prediction: Cat (wrong, it's actually a Dog)
- Adjust: Increase weight of Weight parameter

... repeat with thousands of images ...

After training: Weights are now accurate
```

The weights have learned patterns from data. Just like humans recognize animals after seeing hundreds of examples, neural networks learn from thousands of training examples.

## Multiple Neurons

A neural network doesn't have just one neuron. It has many neurons working together, each learning different patterns.

Each neuron:
- Takes all inputs
- Applies its own learned weights
- Produces its own score
- Contributes to the final decision

## Extending to Language Models (LLMs)

The same principle applies to LLMs:

```
Question: "The sky is __"

Initially:
- Weights are random
- Model predicts: "banana" (wrong)

We tell the model: "No, the answer is 'blue'"

Model adjusts:
- Increase weight of patterns associated with "sky"
- Increase weight of patterns associated with "blue"
- Decrease weight of patterns associated with fruits

Training with millions of examples:
- Weights slowly absorb language patterns
- Model learns that "sky" correlates with colors
- Model learns grammar, facts, reasoning patterns
- Finally, model predicts "blue" correctly
```

## Key Insight

**Neural networks don't follow pre-defined rules. They learn rules from data by adjusting weights.**

1. **Start:** Random weights → bad predictions
2. **Training:** Show millions of examples → adjust weights based on errors
3. **Learned:** Weights capture patterns in data
4. **Result:** Model makes accurate predictions on new data

This is how modern AI works. No programmer tells the model "if X then Y". The model learns from data.


One of the imporant neural network  is the Transformers neural network which with's 'Self Attention' mechanism to process the input data changed the llm landscape all together