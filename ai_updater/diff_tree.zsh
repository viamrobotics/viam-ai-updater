#This zsh script is used to get the diff of the last automatic proto update, as well as the tree structure of the SDK
ZSH_DIFF_OUTPUT=$(git diff workflow/update-proto~1 workflow/update-proto -- ../src/viam/gen/component)
export ZSH_DIFF_OUTPUT
echo Diff output saved and exported to ZSH_DIFF_OUTPUT variable.
TREE_OUTPUT=$(tree ../src/viam)
export TREE_OUTPUT
echo Tree output saved and exported to TREE_OUTPUT variable.
TESTS_TREE_OUTPUT=$(tree ../tests)
export TESTS_TREE_OUTPUT
echo Tests tree output saved and exported to TESTS_TREE_OUTPUT variable.
