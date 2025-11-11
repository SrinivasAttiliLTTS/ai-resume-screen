import React from "react";

const ResultsTable = ({ results }) => {
  if (!results || results.length === 0) return null;

  return (
    <div className="results-table">
      <h3>Analysis Results</h3>
      <table>
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Score</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i}>
              <td>{r.name}</td>
              <td>{r.score}</td>
              <td>{r.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;
